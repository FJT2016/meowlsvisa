"""Admin routes: paginated list + status updates (triggers email/push/PDF background tasks)."""
import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException, Query, Request

from database import db
from models import StatusUpdate, VisaApplication
from services.auth import get_current_user
from services.email import send_approval_email, send_rejection_email
from services.pdf import build_and_persist_visa_pdf
from services.push import send_push_to_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_dates(app: dict) -> dict:
    if isinstance(app.get('created_at'), str):
        app['created_at'] = datetime.fromisoformat(app['created_at'])
    if isinstance(app.get('updated_at'), str):
        app['updated_at'] = datetime.fromisoformat(app['updated_at'])
    return app


@router.get("/admin/applications")
async def get_all_applications(
    request: Request,
    session_token: Optional[str] = Cookie(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Paginated admin listing. When `page` is not supplied, returns the legacy
    flat list (for backwards compat). Supports search (id/name/passport/email/
    nationality — case-insensitive) and status filter."""
    user = await get_current_user(request, session_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Build filter
    mongo_filter: dict = {}
    if status and status != "all":
        mongo_filter["status"] = status
    if search:
        pattern = {"$regex": search.strip(), "$options": "i"}
        mongo_filter["$or"] = [
            {"application_id": pattern},
            {"personal_info.full_name": pattern},
            {"personal_info.passport_number": pattern},
            {"personal_info.email": pattern},
            {"personal_info.nationality": pattern},
        ]

    # Legacy mode: return all (used by older clients / tests)
    if page is None:
        apps = await db.visa_applications.find(
            mongo_filter, {"_id": 0}
        ).sort("created_at", -1).to_list(10000)
        return [VisaApplication(**_parse_dates(a)) for a in apps]

    total = await db.visa_applications.count_documents(mongo_filter)
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    current = min(page, total_pages)
    skip = (current - 1) * page_size
    cursor = (
        db.visa_applications
        .find(mongo_filter, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = [VisaApplication(**_parse_dates(a)) for a in await cursor.to_list(page_size)]
    return {
        "items": items,
        "total": total,
        "page": current,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.put("/admin/applications/{application_id}/status")
async def update_application_status(
    application_id: str,
    status_data: StatusUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": status_data.status,
        "updated_at": now_iso,
        "status_changed_at": now_iso,
        "status_seen_at": None,  # re-unseen on every status flip
    }
    if status_data.notes:
        update_data["admin_notes"] = status_data.notes

    result = await db.visa_applications.update_one(
        {"application_id": application_id}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")

    updated_app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )

    # Kick off async side-effects so the admin PUT returns immediately.
    if status_data.status == "approved":
        # PDF generation happens in the background; email + push trigger after it.
        async def _approve_pipeline():
            await build_and_persist_visa_pdf(application_id)
            fresh = await db.visa_applications.find_one(
                {"application_id": application_id}, {"_id": 0}
            )
            if fresh:
                await send_approval_email(fresh)
                await send_push_to_user(fresh["user_id"], {
                    "title": "Meowls Visa Approved",
                    "body": f"Your {fresh['visa_type'].title()} visa has been approved. Tap to download your visa PDF.",
                    "application_id": application_id,
                    "status": "approved",
                })
        asyncio.create_task(_approve_pipeline())
    elif status_data.status == "rejected":
        asyncio.create_task(send_rejection_email(updated_app, status_data.notes or ""))
        asyncio.create_task(send_push_to_user(updated_app["user_id"], {
            "title": "Meowls Visa Update",
            "body": f"Your visa application ({application_id}) was not approved. Tap to see details.",
            "application_id": application_id,
            "status": "rejected",
        }))

    return {
        "message": "Status updated successfully",
        "email_sent": status_data.status in ["approved", "rejected"],
    }
