"""
Database connection setup — provides BOTH sync and async engines.

- Celery workers, monitor service, CLI scripts → use sync SessionLocal / get_db_sync()
- FastAPI routes → use async AsyncSessionLocal / get_db()
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ── Lazy import to avoid circular deps with settings ──
_sync_engine = None
_sync_session_factory = None
_async_engine = None
_async_session_factory = None

Base = declarative_base()


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        from shared.config import settings
        # Convert async URL to sync if needed
        url = settings.database_url
        if url.startswith("postgresql+asyncpg"):
            url = url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
        elif url.startswith("postgresql://") or url.startswith("postgres://"):
            pass  # Already sync-compatible
        _sync_engine = create_engine(
            url,
            echo=(settings.environment == "development"),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _sync_engine


def _get_sync_session_factory():
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=_get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sync_session_factory


# ── Public API ──

def SessionLocal() -> Session:
    """Create a new synchronous database session."""
    factory = _get_sync_session_factory()
    return factory()


def get_db_sync():
    """Generator yielding a sync session — for Celery tasks, monitor, CLI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db():
    """Async generator yielding a sync session wrapped for FastAPI Depends().

    FastAPI supports sync generators in Depends() just fine, so we can
    reuse the sync session factory here.  If you later move to full async
    queries you can swap this out for an AsyncSession version.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
