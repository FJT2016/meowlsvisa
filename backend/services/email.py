"""Resend email delivery with a retry queue for transient failures."""
import asyncio
import base64
import logging
import uuid
from datetime import datetime, timezone, timedelta
from io import BytesIO

import resend

from config import (
    RESEND_API_KEY, SENDER_EMAIL,
    EMAIL_RETRY_BACKOFF_SECONDS, EMAIL_RETRY_WORKER_INTERVAL_SECONDS,
    EMAIL_RETRY_MAX_ATTEMPTS,
)
from database import db
from services.pdf import generate_visa_document_with_ai, create_visa_pdf

logger = logging.getLogger(__name__)
resend.api_key = RESEND_API_KEY

# Errors that will NEVER succeed no matter how many times we retry:
# Resend's sandbox-mode response about needing domain verification.
PERMANENT_ERROR_MARKERS = (
    "You can only send testing emails to your own email address",
    "verify a domain at resend.com",
    "Invalid `from` field",
    "validation_error",
)


def _is_permanent_error(err: str) -> bool:
    return any(marker in err for marker in PERMANENT_ERROR_MARKERS)


async def _enqueue_retry(params: dict, error: str, previous_attempts: int = 0) -> None:
    """Queue a failed email for later retry unless it's a permanent/sandbox error."""
    if _is_permanent_error(error):
        logger.info(
            f"Email to {params.get('to')} rejected permanently (sandbox / invalid from) — not queuing"
        )
        return
    attempts = previous_attempts + 1
    if attempts > EMAIL_RETRY_MAX_ATTEMPTS:
        logger.error(
            f"Email to {params.get('to')} exhausted {EMAIL_RETRY_MAX_ATTEMPTS} retries — giving up"
        )
        return
    backoff = EMAIL_RETRY_BACKOFF_SECONDS[min(attempts - 1, len(EMAIL_RETRY_BACKOFF_SECONDS) - 1)]
    next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
    await db.email_retry_queue.insert_one({
        "id": f"retry_{uuid.uuid4().hex[:12]}",
        "params": params,
        "attempts": attempts,
        "last_error": error,
        "next_retry_at": next_retry_at.isoformat(),
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(
        f"Queued retry #{attempts} for {params.get('to')} in {backoff}s ({error[:80]})"
    )


async def _send_single(params: dict, previous_attempts: int = 0) -> bool:
    """Send one email. On failure, queue for retry. Returns True on success."""
    try:
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        err = str(e)
        logger.error(f"Email to {params.get('to')} failed: {err}")
        await _enqueue_retry(params, err, previous_attempts=previous_attempts)
        return False


async def _get_admin_emails() -> list:
    admins = await db.users.find({"role": "admin"}, {"_id": 0, "email": 1}).to_list(100)
    return [a["email"] for a in admins]


def _dedupe_recipients(emails: list) -> list:
    seen, out = set(), []
    for e in emails:
        if e and e not in seen:
            out.append(e)
            seen.add(e)
    return out


def _approval_html(application: dict) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;">
      <div style="max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0F172A;color:#fff;padding:30px;text-align:center;border-radius:8px 8px 0 0;">
          <h1 style="margin:0;font-size:28px;">Visa Approved!</h1>
          <p style="margin:10px 0 0;color:#D97706;">Republic of Meowls Immigration</p>
        </div>
        <div style="background:#f8fafc;padding:30px;border-radius:0 0 8px 8px;">
          <p>Dear <strong>{application['personal_info']['full_name']}</strong>,</p>
          <p>Congratulations! Your visa application for the Republic of Meowls has been
          <strong style="color:#166534;">APPROVED</strong>.</p>
          <div style="background:#fff;padding:20px;border-left:4px solid #D97706;margin:20px 0;">
            <p><strong>Application ID:</strong> {application['application_id']}</p>
            <p><strong>Visa Type:</strong> {application['visa_type'].title()}</p>
            <p><strong>Travel Dates:</strong> {application['travel_details']['arrival_date']} to {application['travel_details']['departure_date']}</p>
          </div>
          <p>Your official e-Visa PDF is attached. Print a copy and present it at immigration on arrival.</p>
          <div style="background:#fef3c7;padding:15px;border-radius:6px;margin:20px 0;">
            <p style="margin:0;color:#92400e;font-size:13px;"><strong>Important:</strong> Visa fee payment will be collected at the port of entry.</p>
          </div>
          <p>We look forward to welcoming you to Meowls!</p>
          <p style="font-size:13px;color:#666;margin-top:30px;padding-top:20px;border-top:1px solid #ddd;">
            Best regards,<br><strong>Immigration Department</strong><br>Republic of Meowls
          </p>
        </div>
      </div>
    </body></html>
    """


def _rejection_html(application: dict, notes: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;">
      <div style="max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0F172A;color:#fff;padding:30px;text-align:center;border-radius:8px 8px 0 0;">
          <h1 style="margin:0;font-size:28px;">Visa Application Update</h1>
          <p style="margin:10px 0 0;color:#D97706;">Republic of Meowls Immigration</p>
        </div>
        <div style="background:#f8fafc;padding:30px;border-radius:0 0 8px 8px;">
          <p>Dear <strong>{application['personal_info']['full_name']}</strong>,</p>
          <p>We have reviewed your visa application (ID: <strong>{application['application_id']}</strong>).</p>
          <div style="background:#fee2e2;padding:20px;border-left:4px solid #dc2626;margin:20px 0;border-radius:4px;">
            <p style="margin:0;color:#991b1b;">Unfortunately, we are unable to approve your visa application at this time.</p>
          </div>
          {f'<div style="background:#fff;padding:15px;border-radius:6px;margin:20px 0;"><p style="margin:0;"><strong>Reason:</strong> {notes}</p></div>' if notes else ''}
          <p>You may reapply after addressing any gaps in your application.</p>
          <p style="font-size:13px;color:#666;margin-top:30px;padding-top:20px;border-top:1px solid #ddd;">
            Best regards,<br><strong>Immigration Department</strong><br>Republic of Meowls
          </p>
        </div>
      </div>
    </body></html>
    """


async def send_approval_email(application: dict) -> bool:
    """Send approval email (one per recipient) with visa PDF attached."""
    try:
        # Use the pre-persisted PDF if available; else regenerate.
        visa_doc = application.get("visa_document")
        if visa_doc and visa_doc.get("data"):
            pdf_bytes = base64.b64decode(visa_doc["data"])
        else:
            content = await generate_visa_document_with_ai(application)
            pdf_bytes = create_visa_pdf(content, application).getvalue()

        pdf_list = list(pdf_bytes)
        admins = await _get_admin_emails()
        recipients = _dedupe_recipients(
            [application['personal_info']['email']] + admins
        )

        params_base = {
            "from": SENDER_EMAIL,
            "subject": "Your Meowls Visa is APPROVED!",
            "html": _approval_html(application),
            "attachments": [{
                "filename": f"meowls_visa_{application['application_id']}.pdf",
                "content": pdf_list,
            }],
        }
        successes = 0
        for i, r in enumerate(recipients):
            if await _send_single({**params_base, "to": [r]}):
                successes += 1
            if i < len(recipients) - 1:
                await asyncio.sleep(0.25)  # respect Resend 5 req/s
        logger.info(f"Approval email: {successes}/{len(recipients)} delivered")
        return successes > 0
    except Exception as e:
        logger.error(f"send_approval_email fatal: {e}")
        return False


async def send_rejection_email(application: dict, notes: str = "") -> bool:
    """Send rejection email (one per recipient)."""
    try:
        admins = await _get_admin_emails()
        recipients = _dedupe_recipients(
            [application['personal_info']['email']] + admins
        )
        params_base = {
            "from": SENDER_EMAIL,
            "subject": "Meowls Visa Application Update",
            "html": _rejection_html(application, notes),
        }
        successes = 0
        for i, r in enumerate(recipients):
            if await _send_single({**params_base, "to": [r]}):
                successes += 1
            if i < len(recipients) - 1:
                await asyncio.sleep(0.25)
        logger.info(f"Rejection email: {successes}/{len(recipients)} delivered")
        return successes > 0
    except Exception as e:
        logger.error(f"send_rejection_email fatal: {e}")
        return False


# -----------------------
# Retry worker
# -----------------------
_retry_worker_task = None


async def _process_due_retries() -> None:
    """Find queued emails whose next_retry_at has passed and try again."""
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor = db.email_retry_queue.find(
        {"next_retry_at": {"$lte": now_iso}}, {"_id": 0}
    )
    due = await cursor.to_list(50)
    for item in due:
        # Remove the row; if it fails again, _send_single will re-enqueue a fresh row
        await db.email_retry_queue.delete_one({"id": item["id"]})
        ok = await _send_single(item["params"], previous_attempts=item.get("attempts", 0))
        if ok:
            logger.info(
                f"Retry success for {item['params'].get('to')} after {item.get('attempts')} attempts"
            )


async def _retry_worker_loop() -> None:
    logger.info("Email retry worker started")
    while True:
        try:
            await _process_due_retries()
        except Exception as e:
            logger.error(f"Retry worker iteration failed: {e}")
        await asyncio.sleep(EMAIL_RETRY_WORKER_INTERVAL_SECONDS)


def start_retry_worker() -> None:
    """Spawn the retry loop (idempotent)."""
    global _retry_worker_task
    if _retry_worker_task is None or _retry_worker_task.done():
        _retry_worker_task = asyncio.create_task(_retry_worker_loop())
