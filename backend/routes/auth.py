"""Auth routes: register / login / google session / me / logout."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Cookie, HTTPException, Request, Response

from database import db
from models import SessionData, User, UserLogin, UserRegister
from services.auth import hash_password, verify_password, get_current_user

router = APIRouter()


def _set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )


@router.post("/auth/register")
async def register(user_data: UserRegister, response: Response):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "picture": None,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)

    session_token = f"session_{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _set_session_cookie(response, session_token)

    user_copy = user.copy()
    user_copy.pop('password_hash', None)
    user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
    return User(**user_copy)


@router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_token = f"session_{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _set_session_cookie(response, session_token)

    user_copy = user_doc.copy()
    user_copy.pop('password_hash', None)
    if isinstance(user_copy['created_at'], str):
        user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
    return User(**user_copy)


@router.post("/auth/session")
async def process_google_session(session_data: SessionData, response: Response):
    try:
        ext_response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_data.session_id},
            timeout=10,
        )
        ext_response.raise_for_status()
        data = ext_response.json()

        user_doc = await db.users.find_one({"email": data["email"]}, {"_id": 0})
        if user_doc:
            user_id = user_doc["user_id"]
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"name": data["name"], "picture": data["picture"]}},
            )
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": user_id,
                "email": data["email"],
                "name": data["name"],
                "picture": data["picture"],
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        session_token = data["session_token"]
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        _set_session_cookie(response, session_token)

        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        user_copy = user_doc.copy()
        user_copy.pop('password_hash', None)
        if isinstance(user_copy['created_at'], str):
            user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
        return User(**user_copy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/me")
async def get_me(request: Request, session_token: Optional[str] = Cookie(None)):
    return await get_current_user(request, session_token)


@router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None),
):
    token = session_token
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie(
        key="session_token", path="/", samesite="none", secure=True
    )
    return {"message": "Logged out successfully"}
