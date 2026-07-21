"""
Monitor service — polls all platforms on a schedule, detects scope changes,
and enqueues recon jobs + notifications.
"""

import json
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import joinedload

from shared.database import SessionLocal
from shared.logging import setup_logging, get_logger
from shared.redis_client import get_redis_client
from shared.config import settings
from db.models import Platform, Program, Scope, AuditLog
from connectors.rate_limiter import TokenBucketRateLimiter
from connectors.hackerone import HackerOneConnector
from connectors.bugcrowd import BugcrowdConnector
from connectors.intigriti import IntigritiConnector
from monitor.circuit_breaker import CircuitBreaker
from monitor.differ import compute_scope_hash, diff_program
from scope_parser.normalizer import normalize_scope_item

logger = get_logger("monitor_runner")
circuit_breaker = CircuitBreaker()

CONNECTORS = {
    'hackerone': HackerOneConnector,
    'bugcrowd': BugcrowdConnector,
    'intigriti': IntigritiConnector,
}


def get_connector(platform: Platform):
    """Instantiate the appropriate connector with the platform's rate limit."""
    connector_class = CONNECTORS.get(platform.name.lower())
    if connector_class:
        rate_limiter = TokenBucketRateLimiter(platform.rate_limit_per_min)
        return connector_class(rate_limiter)
    return None


def poll_all_platforms():
    """One full polling cycle across every registered platform."""
    corr_id = uuid.uuid4()
    logger.info("poll_cycle_started", correlation_id=str(corr_id))

    db = SessionLocal()
    redis = get_redis_client()

    try:
        platforms = db.query(Platform).all()
        for platform in platforms:
            if circuit_breaker.is_open(platform.name):
                logger.warning("circuit_open_skipping", platform=platform.name)
                continue

            connector = get_connector(platform)
            if not connector:
                logger.error("no_connector", platform=platform.name)
                continue

            try:
                logger.info("fetching_programs", platform=platform.name)
                raw_programs = connector.fetch_all_programs()

                for raw_program in raw_programs:
                    external_id = str(
                        raw_program.get('id') or raw_program.get('handle', '')
                    )
                    if not external_id:
                        continue

                    # Fetch raw scope from platform API
                    raw_scope = connector.fetch_program_scope(external_id)

                    # Normalize each scope item
                    items = raw_scope if isinstance(raw_scope, list) else []
                    normalized_scope = []
                    for item in items:
                        norm = normalize_scope_item(item, platform.name)
                        if norm:
                            normalized_scope.append(norm)

                    new_scope_hash = compute_scope_hash(normalized_scope)

                    # Look up existing program
                    existing_program = (
                        db.query(Program)
                        .options(joinedload(Program.scopes))
                        .filter(
                            Program.platform_id == platform.id,
                            Program.external_id == external_id,
                        )
                        .first()
                    )

                    diff = diff_program(existing_program, new_scope_hash, normalized_scope)

                    if diff.type in ('new', 'scope_changed'):
                        logger.info(
                            "change_detected",
                            external_id=external_id,
                            change_type=diff.type,
                            added=len(diff.added),
                            removed=len(diff.removed),
                        )

                        if not existing_program:
                            existing_program = Program(
                                platform_id=platform.id,
                                external_id=external_id,
                                name=raw_program.get('name', external_id),
                                url=raw_program.get('url', ''),
                                offers_bounty=raw_program.get('offers_bounty', True),
                                scope_hash=new_scope_hash,
                                raw_scope_json=raw_scope,
                                last_change_type='new',
                            )
                            db.add(existing_program)
                            db.flush()
                        else:
                            existing_program.scope_hash = new_scope_hash
                            existing_program.raw_scope_json = raw_scope
                            existing_program.last_updated = datetime.now(timezone.utc)
                            existing_program.last_change_type = 'scope_changed'
                            # Delete old scopes, insert fresh ones
                            db.query(Scope).filter(
                                Scope.program_id == existing_program.id
                            ).delete()

                        # Insert normalized scope rows (in-scope AND out-of-scope)
                        for scope_data in normalized_scope:
                            db.add(Scope(
                                program_id=existing_program.id,
                                asset_identifier=scope_data['asset_identifier'],
                                asset_type=scope_data['asset_type'],
                                in_scope=scope_data['in_scope'],
                                eligible_for_bounty=scope_data.get('eligible_for_bounty', True),
                                severity_max=scope_data.get('severity_max'),
                                instructions=scope_data.get('instructions'),
                            ))

                        # Push notification to Redis
                        notif = {
                            "program_id": existing_program.id,
                            "program_name": existing_program.name,
                            "type": diff.type,
                            "added": diff.added,
                            "removed": diff.removed,
                        }
                        redis.rpush("notifications", json.dumps(notif))
                        # Also publish for WebSocket live updates
                        redis.publish("platform_updates", json.dumps(notif))

                        # Enqueue recon for in-scope domains/wildcards
                        db.flush()  # ensure scope IDs are assigned
                        for s in db.query(Scope).filter(
                            Scope.program_id == existing_program.id,
                            Scope.in_scope == True,  # noqa: E712
                            Scope.asset_type.in_(['domain', 'wildcard_domain']),
                        ).all():
                            job = {
                                "scope_id": s.id,
                                "correlation_id": str(corr_id),
                            }
                            redis.rpush("recon_jobs", json.dumps(job))

                        # Audit log
                        db.add(AuditLog(
                            correlation_id=corr_id,
                            action="program_upserted",
                            program_id=existing_program.id,
                            detail=notif,
                        ))
                        db.commit()

                platform.last_polled_at = datetime.now(timezone.utc)
                db.commit()
                circuit_breaker.record_success(platform.name)

            except Exception as e:
                logger.error("platform_poll_failed", platform=platform.name, error=str(e))
                circuit_breaker.record_failure(platform.name)
                db.rollback()

    finally:
        db.close()

    logger.info("poll_cycle_finished", correlation_id=str(corr_id))


if __name__ == '__main__':
    setup_logging()
    scheduler = BlockingScheduler()
    scheduler.add_job(
        poll_all_platforms,
        'interval',
        minutes=settings.poll_interval_minutes,
    )
    logger.info("monitor_starting", poll_interval=settings.poll_interval_minutes)
    try:
        poll_all_platforms()  # run once immediately
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("monitor_shutdown")
