import base64
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import structlog
from shared.config import settings

logger = structlog.get_logger(__name__)

def send_email(to: str, subject: str, html: str, attachments: list[dict] | None = None) -> bool:
    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        message = Mail(
            from_email=settings.from_email,
            to_emails=to,
            subject=subject,
            html_content=html
        )

        if attachments:
            for att in attachments:
                attachment = Attachment(
                    FileContent(att['content']),
                    FileName(att['filename']),
                    FileType(att['type']),
                    Disposition('attachment')
                )
                message.add_attachment(attachment)

        response = sg.send(message)
        logger.info("email_sent", to=to, subject=subject, status_code=response.status_code)
        return True
    except Exception as e:
        logger.error("email_send_failed", to=to, subject=subject, error=str(e))
        return False
