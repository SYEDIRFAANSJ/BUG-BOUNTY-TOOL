"""
Recon pipeline — Celery task orchestrating the full recon tool chain.

SAFETY: Step 0 re-reads scope.in_scope from the DB at execution time
(not from whatever was true at enqueue time) and aborts immediately if false.
"""

import uuid
import structlog
from celery import Celery
from shared.config import settings
from shared.database import SessionLocal
from db.models import Scope, Asset, Endpoint, AuditLog
from shared.redis_client import get_redis_client
from recon.tools import (
    subfinder_wrapper, httpx_wrapper, gowitness_wrapper,
    katana_wrapper, gau_wrapper, js_parser
)
from rules_engine.tagger import tag_endpoint
import recon.celeryconfig

logger = structlog.get_logger(__name__)

celery_app = Celery('recon_engine')
celery_app.config_from_object(recon.celeryconfig)
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url


class ReconAbortedError(Exception):
    """Raised when a recon job is attempted on an out-of-scope asset."""
    pass


@celery_app.task(bind=True, max_retries=3, soft_time_limit=1200, time_limit=1500)
def run_recon_pipeline(self, scope_id: int, correlation_id: str):
    """Execute the full recon pipeline for a single scope entry."""
    db = SessionLocal()
    redis = get_redis_client()
    lock_key = f"recon_lock:{scope_id}"
    corr_uuid = uuid.UUID(correlation_id) if isinstance(correlation_id, str) else correlation_id

    try:
        # ───────────────────────────────────────────────────────────
        # Step 0: Guard check — MANDATORY, FIRST LINE, NON-SKIPPABLE
        # Re-read from DB, not from cached/enqueue-time state.
        # ───────────────────────────────────────────────────────────
        scope = db.query(Scope).filter(Scope.id == scope_id).first()
        if not scope or not scope.in_scope:
            db.add(AuditLog(
                correlation_id=corr_uuid,
                action='recon_aborted_out_of_scope',
                program_id=scope.program_id if scope else None,
                detail={'scope_id': scope_id}
            ))
            db.commit()
            raise ReconAbortedError(
                f"Refusing to scan out-of-scope asset: "
                f"{scope.asset_identifier if scope else f'scope_id={scope_id} not found'}"
            )

        domain = scope.asset_identifier.lstrip('*.')
        log = logger.bind(scope_id=scope_id, correlation_id=correlation_id, domain=domain)
        log.info("recon_pipeline_started")

        db.add(AuditLog(
            correlation_id=corr_uuid, action='recon_started',
            program_id=scope.program_id,
            detail={'scope_id': scope_id, 'domain': domain}
        ))
        db.commit()

        # ───────────────────────────────────────────────────────────
        # Step 1: Subdomain enumeration
        # ───────────────────────────────────────────────────────────
        subdomains: list[str] = []
        try:
            db.add(AuditLog(
                correlation_id=corr_uuid, action='tool_started',
                program_id=scope.program_id,
                detail={'tool': 'subfinder', 'domain': domain}
            ))
            db.commit()
            subdomains = subfinder_wrapper.run(domain, timeout=settings.subprocess_timeout_seconds)
            for sub in subdomains:
                existing = db.query(Asset).filter(
                    Asset.scope_id == scope_id, Asset.subdomain == sub
                ).first()
                if not existing:
                    db.add(Asset(scope_id=scope_id, subdomain=sub))
            db.commit()
            log.info("subfinder_complete", count=len(subdomains))
        except Exception as e:
            log.error("subfinder_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 2: Liveness + tech fingerprint
        # ───────────────────────────────────────────────────────────
        live_subdomains: list[str] = []
        try:
            db.add(AuditLog(
                correlation_id=corr_uuid, action='tool_started',
                program_id=scope.program_id,
                detail={'tool': 'httpx', 'target_count': len(subdomains)}
            ))
            db.commit()
            httpx_results = httpx_wrapper.run(subdomains, timeout=settings.subprocess_timeout_seconds)
            for res in httpx_results:
                asset = db.query(Asset).filter(
                    Asset.scope_id == scope_id, Asset.subdomain == res['url']
                ).first()
                if asset:
                    asset.is_live = res.get('is_live', False)
                    asset.http_status = res.get('status_code')
                    asset.tech_stack = res.get('tech', [])
                    asset.title = res.get('title')
                    if asset.is_live:
                        live_subdomains.append(asset.subdomain)
            db.commit()
            log.info("httpx_complete", live_count=len(live_subdomains))
        except Exception as e:
            log.error("httpx_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 3: Screenshot (live assets only)
        # ───────────────────────────────────────────────────────────
        try:
            if live_subdomains:
                db.add(AuditLog(
                    correlation_id=corr_uuid, action='tool_started',
                    program_id=scope.program_id,
                    detail={'tool': 'gowitness', 'target_count': len(live_subdomains)}
                ))
                db.commit()
                screenshots = gowitness_wrapper.run(live_subdomains, timeout=settings.subprocess_timeout_seconds)
                for url, path in screenshots.items():
                    asset = db.query(Asset).filter(
                        Asset.scope_id == scope_id, Asset.subdomain == url
                    ).first()
                    if asset:
                        asset.screenshot_path = path
                db.commit()
                log.info("gowitness_complete", screenshots=len(screenshots))
        except Exception as e:
            log.error("gowitness_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 4: Endpoint / URL discovery (katana + gau, merged)
        # ───────────────────────────────────────────────────────────
        discovered_endpoints: list[dict] = []
        try:
            db.add(AuditLog(
                correlation_id=corr_uuid, action='tool_started',
                program_id=scope.program_id,
                detail={'tool': 'katana+gau', 'domain': domain}
            ))
            db.commit()
            discovered_endpoints.extend(katana_wrapper.run(live_subdomains, timeout=settings.subprocess_timeout_seconds))
            discovered_endpoints.extend(gau_wrapper.run(domain, timeout=settings.subprocess_timeout_seconds))
            # Dedupe by URL
            discovered_endpoints = list({ep['url']: ep for ep in discovered_endpoints}.values())

            # Get asset IDs for linking
            scope_assets = db.query(Asset).filter(Asset.scope_id == scope_id).all()
            asset_map = {a.subdomain: a.id for a in scope_assets}

            for ep_data in discovered_endpoints:
                if not db.query(Endpoint).filter(Endpoint.url == ep_data['url']).first():
                    # Try to match to an asset
                    matched_asset_id = None
                    for sub, aid in asset_map.items():
                        if sub and sub in ep_data['url']:
                            matched_asset_id = aid
                            break
                    db.add(Endpoint(
                        asset_id=matched_asset_id,
                        url=ep_data['url'],
                        method=ep_data.get('method', 'GET'),
                        params=ep_data.get('params', []),
                        discovered_via=ep_data.get('discovered_via', 'katana')
                    ))
            db.commit()
            log.info("endpoint_discovery_complete", count=len(discovered_endpoints))
        except Exception as e:
            log.error("endpoint_discovery_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 5: JS endpoint mining
        # ───────────────────────────────────────────────────────────
        try:
            js_urls = [ep['url'] for ep in discovered_endpoints
                       if ep['url'].endswith('.js') or 'javascript' in ep.get('content_type', '')]
            if js_urls:
                db.add(AuditLog(
                    correlation_id=corr_uuid, action='tool_started',
                    program_id=scope.program_id,
                    detail={'tool': 'js_parser', 'js_file_count': len(js_urls)}
                ))
                db.commit()
                new_eps = js_parser.extract_from_js(js_urls)
                for ep_data in new_eps:
                    if not db.query(Endpoint).filter(Endpoint.url == ep_data['url']).first():
                        db.add(Endpoint(
                            url=ep_data['url'],
                            method='GET',
                            params=ep_data.get('params', []),
                            discovered_via='js_parse'
                        ))
                db.commit()
                log.info("js_parser_complete", new_endpoints=len(new_eps))
        except Exception as e:
            log.error("js_parser_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 6: Tagging (scope-specific endpoints only)
        # ───────────────────────────────────────────────────────────
        try:
            # Get only endpoints belonging to assets in this scope
            scope_asset_ids = [a.id for a in db.query(Asset).filter(Asset.scope_id == scope_id).all()]
            scope_endpoints = db.query(Endpoint).filter(
                Endpoint.asset_id.in_(scope_asset_ids)
            ).all() if scope_asset_ids else []
            # Also tag any unlinked endpoints (asset_id=None) discovered in this run
            unlinked = db.query(Endpoint).filter(Endpoint.asset_id.is_(None)).all()
            all_eps = list(scope_endpoints) + list(unlinked)

            for ep in all_eps:
                ep_data = {
                    'url': ep.url,
                    'params': ep.params or [],
                    'method': ep.method or 'GET',
                    'content_type': ep.content_type or '',
                    'tech_stack': []
                }
                tags, risk = tag_endpoint(ep_data)
                ep.test_tags = tags
                ep.risk_priority = risk
            db.commit()
            log.info("tagging_complete", endpoints_tagged=len(all_eps))
        except Exception as e:
            log.error("tagging_failed", error=str(e))

        # ───────────────────────────────────────────────────────────
        # Step 7: Audit + enqueue report generation
        # ───────────────────────────────────────────────────────────
        total_assets = db.query(Asset).filter(Asset.scope_id == scope_id).count()
        total_endpoints = len(all_eps) if 'all_eps' in dir() else 0
        db.add(AuditLog(
            correlation_id=corr_uuid, action='recon_completed',
            program_id=scope.program_id,
            detail={
                'scope_id': scope_id,
                'domain': domain,
                'total_assets': total_assets,
                'total_endpoints': total_endpoints
            }
        ))
        db.commit()
        log.info("recon_pipeline_completed", total_assets=total_assets, total_endpoints=total_endpoints)

    except ReconAbortedError:
        raise  # Let Celery see this as a permanent failure, don't retry
    except Exception as exc:
        logger.error("recon_pipeline_error", scope_id=scope_id, error=str(exc))
        raise self.retry(exc=exc)
    finally:
        redis.delete(lock_key)
        db.close()


def enqueue_recon_job(scope_id: int, correlation_id: str) -> bool:
    """Enqueue a recon job with Redis NX lock for idempotency (30min TTL)."""
    redis = get_redis_client()
    lock_key = f"recon_lock:{scope_id}"
    if redis.set(lock_key, correlation_id, nx=True, ex=1800):
        run_recon_pipeline.delay(scope_id, correlation_id)
        logger.info("recon_job_enqueued", scope_id=scope_id, correlation_id=correlation_id)
        return True
    logger.info("recon_already_queued", scope_id=scope_id)
    return False
