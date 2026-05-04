"""In-app notifications + visa PDF download for applicants."""
import base64
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from fastapi.responses import StreamingResponse

from database import db
from services.auth import get_current_user
from services.pdf import generate_visa_document_with_ai, create_visa_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/notifications")
async def get_notifications(
    request: Request, session_token: Optional[str] = Cookie(None)
):
    user = await get_current_user(request, session_token)
    cursor = db.visa_applications.find(
        {
            "user_id": user.user_id,
            "status": {"$in": ["approved", "rejected"]},
            "status_seen_at": None,
        },
        {"_id": 0, "application_id": 1, "visa_type": 1, "status": 1,
         "status_changed_at": 1, "admin_notes": 1},
    )
    items = await cursor.to_list(100)
    return {"unread": items, "count": len(items)}


@router.post("/notifications/{application_id}/read")
async def mark_notification_read(
    application_id: str,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    result = await db.visa_applications.update_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"$set": {"status_seen_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"ok": True}


@router.get("/applications/{application_id}/visa-pdf")
async def download_visa_pdf(
    application_id: str,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    app_doc = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app_doc:
        raise HTTPException(status_code=404, detail="Application not found")
    if app_doc["user_id"] != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if app_doc.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Visa not approved yet")

    visa_doc = app_doc.get("visa_document")
    if not visa_doc or not visa_doc.get("data"):
        # Generate on demand (covers pre-feature approvals or background task lag)
        try:
            content = await generate_visa_document_with_ai(app_doc)
            pdf_bytes = create_visa_pdf(content, app_doc).getvalue()
            pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
            visa_doc = {
                "filename": f"meowls_visa_{application_id}.pdf",
                "content_type": "application/pdf",
                "data": pdf_b64,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.visa_applications.update_one(
                {"application_id": application_id},
                {"$set": {"visa_document": visa_doc}},
            )
        except Exception as e:
            logger.error(f"On-demand PDF generation failed: {e}")
            raise HTTPException(status_code=500, detail="Could not generate visa document")
    else:
        pdf_bytes = base64.b64decode(visa_doc["data"])

    filename = visa_doc.get("filename", f"meowls_visa_{application_id}.pdf")
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
