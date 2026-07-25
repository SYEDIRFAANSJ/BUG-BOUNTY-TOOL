"""
FastAPI application entrypoint.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.logging import setup_logging, get_logger
from shared.database import Base, _get_sync_engine
from api.routes import auth, programs, watchlist, ws

logger = get_logger(__name__)

# PDF output directory — relative to project root, works inside Docker too
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "reports" / "pdfs"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create dirs, tables, mount static files."""
    setup_logging()

    # Create the PDF output directory
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Create all database tables if they don't exist yet
    engine = _get_sync_engine()
    # Import all models so Base.metadata knows about them
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_ready")

    # Seed platforms if empty
    _seed_platforms_if_empty()

    # Mount static file serving for PDF reports (directory now exists)
    app.mount("/reports/pdfs", StaticFiles(directory=str(PDF_DIR)), name="pdfs")

    logger.info("api_started", pdf_dir=str(PDF_DIR))
    yield


def _seed_platforms_if_empty():
    """Insert default platforms if the platforms table is empty."""
    from shared.database import SessionLocal
    from db.models import Platform

    db = SessionLocal()
    try:
        count = db.query(Platform).count()
        if count == 0:
            platforms = [
                Platform(
                    name="hackerone",
                    api_base_url="https://api.hackerone.com/v1",
                    rate_limit_per_min=50,
                    poll_interval_minutes=60,
                ),
                Platform(
                    name="bugcrowd",
                    api_base_url="https://api.bugcrowd.com",
                    rate_limit_per_min=60,
                    poll_interval_minutes=60,
                ),
                Platform(
                    name="intigriti",
                    api_base_url="https://api.intigriti.com/external/researcher",
                    rate_limit_per_min=30,
                    poll_interval_minutes=60,
                ),
            ]
            db.add_all(platforms)
            db.commit()
            logger.info("platforms_seeded", count=len(platforms))
    except Exception as e:
        db.rollback()
        logger.error("seed_failed", error=str(e))
    finally:
        db.close()


app = FastAPI(
    title="Bug Bounty Recon Platform API",
    version="1.0.0",
    description="Authorized security research reconnaissance platform",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(auth.router,      prefix="/auth",      tags=["auth"])
app.include_router(programs.router,   prefix="/programs",  tags=["programs"])
app.include_router(watchlist.router,                       tags=["watchlist"])
app.include_router(ws.router,         prefix="/ws",        tags=["websocket"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
