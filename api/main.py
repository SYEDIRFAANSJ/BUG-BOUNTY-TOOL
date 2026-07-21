"""
FastAPI application entrypoint.
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.logging import setup_logging, get_logger
from api.routes import auth, programs, watchlist, ws

logger = get_logger(__name__)

# PDF output directory — relative to project root, works inside Docker too
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "reports" / "pdfs"

app = FastAPI(
    title="Bug Bounty Recon Platform API",
    version="1.0.0",
    description="Authorized security research reconnaissance platform",
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ──
@app.on_event("startup")
async def startup_event():
    setup_logging()
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("api_started", pdf_dir=str(PDF_DIR))

# ── Routes ──
app.include_router(auth.router,      prefix="/auth",      tags=["auth"])
app.include_router(programs.router,   prefix="/programs",  tags=["programs"])
app.include_router(watchlist.router,                       tags=["watchlist"])
app.include_router(ws.router,         prefix="/ws",        tags=["websocket"])

# ── Static file serving for PDF reports ──
app.mount("/reports/pdfs", StaticFiles(directory=str(PDF_DIR)), name="pdfs")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
