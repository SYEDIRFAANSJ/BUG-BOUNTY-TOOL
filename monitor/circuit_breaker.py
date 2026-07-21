"""
Circuit breaker — protects the monitor from hammering a failing platform API.
After `failure_threshold` consecutive failures, the circuit opens for
`reset_timeout_minutes` and all requests to that platform are skipped.
"""

import uuid
from datetime import datetime, timedelta, timezone

from shared.logging import get_logger

logger = get_logger("circuit_breaker")


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout_minutes: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout_minutes = reset_timeout_minutes
        self.failures: dict[str, int] = {}
        self.open_until: dict[str, datetime] = {}

    def is_open(self, platform_name: str) -> bool:
        if platform_name in self.open_until:
            if datetime.now(timezone.utc) < self.open_until[platform_name]:
                return True
            else:
                del self.open_until[platform_name]
                self.failures[platform_name] = 0
        return False

    def record_success(self, platform_name: str):
        self.failures[platform_name] = 0
        self.open_until.pop(platform_name, None)

    def record_failure(self, platform_name: str):
        count = self.failures.get(platform_name, 0) + 1
        self.failures[platform_name] = count

        if count >= self.failure_threshold:
            self.open_until[platform_name] = (
                datetime.now(timezone.utc)
                + timedelta(minutes=self.reset_timeout_minutes)
            )
            self._log_circuit_tripped(platform_name)

    def _log_circuit_tripped(self, platform_name: str):
        """Write an audit_log entry when the circuit trips."""
        try:
            from shared.database import SessionLocal
            from db.models import AuditLog

            db = SessionLocal()
            try:
                db.add(AuditLog(
                    correlation_id=uuid.uuid4(),
                    action='circuit_tripped',
                    detail={
                        "platform": platform_name,
                        "reason": f"Consecutive failures >= {self.failure_threshold}",
                        "open_for_minutes": self.reset_timeout_minutes,
                    },
                ))
                db.commit()
            finally:
                db.close()
            logger.warning(
                "circuit_tripped",
                platform=platform_name,
                open_minutes=self.reset_timeout_minutes,
            )
        except Exception as e:
            logger.error("circuit_trip_log_failed", error=str(e))
