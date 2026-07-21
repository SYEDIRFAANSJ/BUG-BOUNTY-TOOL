"""
Email worker — Celery tasks for instant alerts, report emails, and digests.
"""

import base64
from pathlib import Path

import jinja2
from celery import Celery
import structlog

from shared.config import settings
from shared.database import SessionLocal
from db.models import User, Program, Report, UserWatchlist
from email_worker.client import send_email

logger = structlog.get_logger(__name__)

celery_app = Celery(
    'email_worker',
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Load Jinja2 templates from the reports/templates directory
_template_dir = Path(__file__).resolve().parent.parent / "reports" / "templates"
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_template_dir))
)


@celery_app.task
def send_instant_alert(program_id: int, diff_type: str, diff_detail: dict):
    """Send an instant email alert when a program is new or scope changes."""
    db = SessionLocal()
    try:
        program = db.query(Program).filter(Program.id == program_id).first()
        if not program:
            logger.warning("alert_program_not_found", program_id=program_id)
            return

        # Users who want instant notifications
        users = db.query(User).filter(User.notify_instant == True).all()  # noqa: E712
        template = template_env.get_template('alert_email.html.j2')

        subject = (
            f"New Program: {program.name}"
            if diff_type == 'new'
            else f"Scope Updated: {program.name}"
        )
        html_content = template.render(
            program_name=program.name,
            platform=program.platform.name if program.platform else 'Unknown',
            diff_type=diff_type,
            diff_detail=diff_detail,
            dashboard_url=f"http://localhost:3000/programs/{program.id}",
        )

        for user in users:
            # Skip muted programs
            muted = (
                db.query(UserWatchlist)
                .filter(
                    UserWatchlist.user_id == user.id,
                    UserWatchlist.program_id == program_id,
                    UserWatchlist.muted == True,  # noqa: E712
                )
                .first()
            )
            if muted:
                continue
            send_email(user.email, subject, html_content)

        logger.info("alerts_sent", program_id=program_id, recipients=len(users))
    except Exception as e:
        logger.error("alert_failed", error=str(e))
    finally:
        db.close()


@celery_app.task
def send_report_email(report_id: int):
    """Send report email with PDF attachment to eligible users."""
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.warning("report_not_found", report_id=report_id)
            return

        program = db.query(Program).filter(Program.id == report.program_id).first()
        program_name = program.name if program else "Unknown Program"

        # Only users with instant digest receive immediately
        users = (
            db.query(User)
            .filter(User.digest_freq.notin_(['daily', 'weekly']))
            .all()
        )

        template = template_env.get_template('report_email.html.j2')
        html_content = template.render(
            program_name=program_name,
            total_assets=report.total_assets,
            total_endpoints=report.total_endpoints,
            high_priority_count=report.high_priority_count,
            summary_json=report.summary_json,
            dashboard_url=f"http://localhost:3000/reports/{report.id}",
        )

        attachments = []
        if report.pdf_path:
            pdf = Path(report.pdf_path)
            if pdf.exists():
                content = base64.b64encode(pdf.read_bytes()).decode('utf-8')
                attachments.append({
                    'filename': f"recon_report_{report.id}.pdf",
                    'content': content,
                    'type': 'application/pdf',
                })

        for user in users:
            send_email(
                user.email,
                f"Recon Report: {program_name}",
                html_content,
                attachments,
            )

        logger.info("report_emails_sent", report_id=report_id, recipients=len(users))
    except Exception as e:
        logger.error("report_email_failed", error=str(e))
    finally:
        db.close()


@celery_app.task
def send_digest():
    """Send aggregated digest emails for daily/weekly users."""
    db = SessionLocal()
    try:
        # TODO: Implement digest aggregation
        # - Query reports created since last digest
        # - Group by user
        # - Render and send bundled email
        logger.info("digest_task_placeholder")
    finally:
        db.close()
