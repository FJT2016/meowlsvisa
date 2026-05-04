"""Pydantic request/response models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "user"
    created_at: datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class SessionData(BaseModel):
    session_id: str


class VisaApplication(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_id: str
    user_id: str
    visa_type: str
    status: str
    personal_info: dict
    travel_details: dict
    documents: dict
    created_at: datetime
    updated_at: datetime
    admin_notes: Optional[str] = None
    visa_document: Optional[dict] = None
    status_changed_at: Optional[str] = None
    status_seen_at: Optional[str] = None


class ApplicationCreate(BaseModel):
    visa_type: str
    personal_info: dict
    travel_details: dict


class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict
