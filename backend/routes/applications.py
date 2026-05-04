"""User-side application routes: create / list / get / update / upload docs / submit."""
import base64
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, File, HTTPException, Request, UploadFile

from database import db
from models import ApplicationCreate, VisaApplication
from services.auth import get_current_user

router = APIRouter()


def _parse_datetimes(app: dict) -> dict:
    if isinstance(app.get('created_at'), str):
        app['created_at'] = datetime.fromisoformat(app['created_at'])
    if isinstance(app.get('updated_at'), str):
        app['updated_at'] = datetime.fromisoformat(app['updated_at'])
    return app


@router.post("/applications")
async def create_application(
    app_data: ApplicationCreate,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    application_id = f"app_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    application = {
        "application_id": application_id,
        "user_id": user.user_id,
        "visa_type": app_data.visa_type,
        "status": "draft",
        "personal_info": app_data.personal_info,
        "travel_details": app_data.travel_details,
        "documents": {},
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.visa_applications.insert_one(application)
    return VisaApplication(**_parse_datetimes(application.copy()))


@router.get("/applications")
async def get_applications(
    request: Request, session_token: Optional[str] = Cookie(None)
):
    user = await get_current_user(request, session_token)
    apps = await db.visa_applications.find(
        {"user_id": user.user_id}, {"_id": 0}
    ).to_list(1000)
    return [VisaApplication(**_parse_datetimes(a)) for a in apps]


@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_id"] != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return VisaApplication(**_parse_datetimes(app))


@router.put("/applications/{application_id}")
async def update_application(
    application_id: str,
    app_data: ApplicationCreate,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "visa_type": app_data.visa_type,
            "personal_info": app_data.personal_info,
            "travel_details": app_data.travel_details,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    updated = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    return VisaApplication(**_parse_datetimes(updated))


@router.post("/applications/{application_id}/documents")
async def upload_document(
    application_id: str,
    file: UploadFile = File(...),
    doc_type: str = "passport",
    request: Request = None,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    content = await file.read()
    encoded = base64.b64encode(content).decode('utf-8')
    await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": {
            f"documents.{doc_type}": {
                "filename": file.filename,
                "content_type": file.content_type,
                "data": encoded,
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {"message": "Document uploaded successfully", "doc_type": doc_type}


@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: str,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    app = await db.visa_applications.find_one(
        {"application_id": application_id}, {"_id": 0}
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "status": "submitted",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {"message": "Application submitted successfully"}
