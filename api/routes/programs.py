"""
Program routes — list, detail, assets, endpoints, reports, PDF download.
"""

from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from api.schemas import (
    ProgramListResponse, ProgramDetail,
    AssetResponse, EndpointResponse, ReportResponse,
)
from api.deps import get_db
from db.models import Program, Scope, Asset, Endpoint, Report
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=ProgramListResponse)
def list_programs(
    skip: int = 0,
    limit: int = 50,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    last_change_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List programs with optional filters and pagination."""
    query = db.query(Program).options(joinedload(Program.platform))
    if platform:
        query = query.filter(Program.platform.has(name=platform))
    if status:
        query = query.filter(Program.status == status)
    if last_change_type:
        query = query.filter(Program.last_change_type == last_change_type)

    total = query.count()
    programs = query.offset(skip).limit(limit).all()
    return {"programs": programs, "total": total}


@router.get("/{id}", response_model=ProgramDetail)
def get_program(id: int, db: Session = Depends(get_db)):
    """Get program detail including scope items."""
    program = (
        db.query(Program)
        .options(joinedload(Program.platform), joinedload(Program.scopes))
        .filter(Program.id == id)
        .first()
    )
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.get("/{id}/assets", response_model=List[AssetResponse])
def get_program_assets(id: int, db: Session = Depends(get_db)):
    """Get all discovered assets for a program."""
    assets = (
        db.query(Asset)
        .join(Scope)
        .filter(Scope.program_id == id)
        .all()
    )
    return assets


@router.get("/{id}/endpoints", response_model=List[EndpointResponse])
def get_program_endpoints(
    id: int,
    risk_priority: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all endpoints for a program, optionally filtered by risk level."""
    query = (
        db.query(Endpoint)
        .join(Asset)
        .join(Scope)
        .filter(Scope.program_id == id)
    )
    if risk_priority:
        query = query.filter(Endpoint.risk_priority == risk_priority)
    return query.all()


@router.get("/{id}/reports", response_model=List[ReportResponse])
def get_program_reports(id: int, db: Session = Depends(get_db)):
    """Get report history for a program."""
    return (
        db.query(Report)
        .filter(Report.program_id == id)
        .order_by(Report.generated_at.desc())
        .all()
    )


@router.get("/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Serve a report PDF file for download."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="Report PDF not found")

    pdf_path = Path(report.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report PDF file missing")

    return FileResponse(
        path=str(pdf_path),
        filename=pdf_path.name,
        media_type="application/pdf",
    )
