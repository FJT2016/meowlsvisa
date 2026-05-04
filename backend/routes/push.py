"""Web push: public key + subscribe / unsubscribe."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request

from config import VAPID_PUBLIC_KEY
from database import db
from models import PushSubscription
from services.auth import get_current_user

router = APIRouter()


@router.get("/push/vapid-public-key")
async def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return {"public_key": VAPID_PUBLIC_KEY}


@router.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": {
            "user_id": user.user_id,
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"ok": True}


@router.post("/push/unsubscribe")
async def unsubscribe_push(
    subscription: PushSubscription,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    await db.push_subscriptions.delete_one(
        {"endpoint": subscription.endpoint, "user_id": user.user_id}
    )
    return {"ok": True}
