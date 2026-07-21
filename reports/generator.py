"""
Report generator — queries recon results for a program, renders an HTML
report via Jinja2, converts to PDF via WeasyPrint, and saves to DB.
"""

import datetime
from pathlib import Path
from collections import Counter

from jinja2 import Environment, FileSystemLoader
import weasyprint

from shared.database import SessionLocal
from db.models import Program, Scope, Asset, Endpoint, Report
from shared.logging import get_logger

logger = get_logger(__name__)

TAG_DESCRIPTIONS = {
    'open_redirect': 'Test redirect parameters with external URLs to check for open redirect vulnerabilities.',
    'ssrf': 'Test URL/webhook parameters with internal IP ranges (127.0.0.1, 169.254.169.254) to detect SSRF.',
    'idor': 'Try incrementing/decrementing numeric ID params while authenticated as a different user to check for broken object-level authorization.',
    'file_upload_rce': 'Test file upload functionality with various file types (.php, .jsp, .svg) to check for unrestricted file upload.',
    'sqli_candidate': 'Test injectable parameters with single quotes and common SQL injection payloads to detect SQL injection.',
    'xxe': 'Test XML endpoints with XXE payloads to check for XML External Entity injection.',
    'graphql_introspection': 'Send introspection queries to enumerate the GraphQL schema and check for exposed sensitive queries/mutations.',
    'auth_bypass_candidate': 'Test admin/internal panels for authentication bypass, default credentials, and horizontal privilege escalation.',
    'secret_exposure': 'Review JavaScript files and responses for exposed API keys, tokens, and credentials.',
    'cors_misconfig': 'Test CORS headers with various Origin values to check for misconfigured cross-origin resource sharing.',
    'jwt_vuln_candidate': 'Test JWT tokens for algorithm confusion (none, HS256/RS256 swap), weak signing keys, and missing expiration.',
    'lfi_candidate': 'Test file/path parameters with path traversal sequences (../../etc/passwd) to detect Local File Inclusion.',
    'cve_check_wordpress': 'Check WordPress version against known CVEs. Test for common WordPress vulnerabilities.',
    'source_disclosure': 'Verify if .git/config or .git/HEAD are accessible. If exposed, the full source code may be downloadable.',
}


def generate_report(program_id: int) -> Report:
    """Generate a PDF recon report for the given program and persist it."""
    logger.info("report_generation_started", program_id=program_id)
    db = SessionLocal()
    try:
        program = db.query(Program).filter(Program.id == program_id).first()
        if not program:
            raise ValueError(f"Program {program_id} not found")

        # In-scope scopes only
        scopes = (
            db.query(Scope)
            .filter(Scope.program_id == program_id, Scope.in_scope == True)  # noqa: E712
            .all()
        )
        scope_ids = [s.id for s in scopes]

        # Assets across those scopes
        assets = db.query(Asset).filter(Asset.scope_id.in_(scope_ids)).all() if scope_ids else []
        asset_ids = [a.id for a in assets]

        # Endpoints across those assets
        endpoints = db.query(Endpoint).filter(Endpoint.asset_id.in_(asset_ids)).all() if asset_ids else []

        total_assets = len(assets)
        total_endpoints = len(endpoints)
        high_priority_count = sum(1 for e in endpoints if e.risk_priority == 'high')

        # Break endpoints into risk buckets
        high_endpoints = [e for e in endpoints if e.risk_priority == 'high']
        medium_endpoints = [e for e in endpoints if e.risk_priority == 'medium']
        low_endpoints = [e for e in endpoints if e.risk_priority == 'low']

        # Aggregate tag counts
        tag_counts: dict[str, int] = Counter()
        for ep in endpoints:
            if ep.test_tags:
                for tag in ep.test_tags:
                    tag_counts[tag] += 1

        summary_json = {
            "risk_priority": {
                "high": len(high_endpoints),
                "medium": len(medium_endpoints),
                "low": len(low_endpoints),
            },
            "tags": dict(tag_counts),
        }

        # ── Render HTML ──
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("recon_report.html.j2")

        now = datetime.datetime.now(datetime.timezone.utc)
        html_content = template.render(
            program=program,
            scopes=scopes,
            assets=assets,
            high_endpoints=high_endpoints,
            medium_endpoints=medium_endpoints,
            low_endpoints=low_endpoints,
            total_assets=total_assets,
            total_endpoints=total_endpoints,
            high_priority_count=high_priority_count,
            tag_counts=tag_counts,
            tag_descriptions=TAG_DESCRIPTIONS,
            date=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        # ── Write PDF ──
        pdfs_dir = Path(__file__).parent / "pdfs"
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        pdf_filename = f"{program_id}_{now.strftime('%Y%m%d%H%M%S')}.pdf"
        pdf_path = pdfs_dir / pdf_filename

        weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
        logger.info("pdf_written", path=str(pdf_path))

        # ── Persist report row ──
        report = Report(
            program_id=program_id,
            total_assets=total_assets,
            total_endpoints=total_endpoints,
            high_priority_count=high_priority_count,
            summary_json=summary_json,
            pdf_path=str(pdf_path),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info("report_saved", report_id=report.id)
        return report

    finally:
        db.close()
