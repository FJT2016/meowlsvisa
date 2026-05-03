from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Cookie, Response, Request
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json as json_lib
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import base64
import requests
import asyncio
import resend
from pywebpush import webpush, WebPushException
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

resend.api_key = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_CLAIMS_SUB = os.environ.get('VAPID_CLAIMS_SUB', 'mailto:admin@meowls.gov')

app = FastAPI()
api_router = APIRouter(prefix="/api")

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

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> User:
    token = session_token
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return User(**user_doc)

async def generate_visa_document_with_ai(application: dict) -> str:
    """Generate visa document content using AI"""
    try:
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"visa_{application['application_id']}",
            system_message="You are an official document generator for the Republic of Meowls Immigration Department. Generate formal, professional visa documents."
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(
            text=f"""Generate a professional visa approval document with the following details:

Applicant Name: {application['personal_info']['full_name']}
Nationality: {application['personal_info']['nationality']}
Passport Number: {application['personal_info']['passport_number']}
Visa Type: {application['visa_type'].title()}
Purpose: {application['travel_details']['purpose']}
Arrival Date: {application['travel_details']['arrival_date']}
Departure Date: {application['travel_details']['departure_date']}
Application ID: {application['application_id']}

Create a formal visa approval letter that includes:
1. Official letterhead greeting
2. Approval statement
3. Visa validity details
4. Important notes about payment at immigration
5. Professional closing

Keep it concise and professional - max 300 words."""
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logger.error(f"AI generation failed: {str(e)}")
        return f"""REPUBLIC OF MEOWLS
IMMIGRATION DEPARTMENT

VISA APPROVAL NOTICE

Application ID: {application['application_id']}
Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}

Dear {application['personal_info']['full_name']},

We are pleased to inform you that your {application['visa_type'].title()} visa application has been APPROVED.

Applicant Details:
- Name: {application['personal_info']['full_name']}
- Nationality: {application['personal_info']['nationality']}
- Passport: {application['personal_info']['passport_number']}
- Visa Type: {application['visa_type'].title()}

Travel Details:
- Arrival: {application['travel_details']['arrival_date']}
- Departure: {application['travel_details']['departure_date']}
- Purpose: {application['travel_details']['purpose']}

IMPORTANT: Please proceed to immigration upon arrival. Visa fee payment will be collected at the port of entry.

Welcome to Meowls!

Immigration Department
Republic of Meowls"""

def create_visa_pdf(content: str, application: dict) -> BytesIO:
    """Create a PDF visa document"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#D97706'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    story = []
    
    story.append(Paragraph("REPUBLIC OF MEOWLS", title_style))
    story.append(Paragraph("Official e-Visa Document", header_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Add applicant photo if available
    try:
        if application.get('documents', {}).get('photo'):
            photo_data = application['documents']['photo']
            if isinstance(photo_data, dict) and 'data' in photo_data:
                import base64
                photo_bytes = base64.b64decode(photo_data['data'])
                photo_buffer = BytesIO(photo_bytes)
                
                # Create photo with border
                img = RLImage(photo_buffer, width=1.5*inch, height=1.5*inch)
                
                # Center the photo
                photo_table = Table([[img]], colWidths=[1.5*inch])
                photo_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0F172A'))
                ]))
                story.append(photo_table)
                story.append(Spacer(1, 0.2*inch))
    except Exception as e:
        logger.error(f"Failed to add photo to PDF: {str(e)}")
    
    for line in content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, body_style))
    
    story.append(Spacer(1, 0.5*inch))
    
    data = [
        ['Application ID:', application['application_id']],
        ['Issue Date:', datetime.now(timezone.utc).strftime('%B %d, %Y')],
        ['Status:', 'APPROVED']
    ]
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0'))
    ]))
    
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

async def send_approval_email(application: dict):
    """Send visa approval email with AI-generated document.
    Sends an individual email to each recipient so that one failure (e.g. Resend
    sandbox restrictions) does not block delivery to other recipients.
    """
    try:
        visa_content = await generate_visa_document_with_ai(application)
        pdf_buffer = create_visa_pdf(visa_content, application)
        pdf_bytes = list(pdf_buffer.getvalue())
        
        # Get all admin emails to include in recipients
        admin_users = await db.users.find({"role": "admin"}, {"_id": 0, "email": 1}).to_list(100)
        admin_emails = [admin["email"] for admin in admin_users]
        
        applicant_email = application['personal_info']['email']
        # Applicant first, then admins (dedupe, preserve order)
        all_recipients = []
        for e in [applicant_email] + admin_emails:
            if e and e not in all_recipients:
                all_recipients.append(e)
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #0F172A; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🎉 Visa Approved!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; color: #D97706;">Republic of Meowls Immigration</p>
                </div>
                
                <div style="background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{application['personal_info']['full_name']}</strong>,</p>
                    
                    <p style="font-size: 14px; margin-bottom: 15px;">Congratulations! Your visa application for the Republic of Meowls has been <strong style="color: #166534;">APPROVED</strong>.</p>
                    
                    <div style="background-color: white; padding: 20px; border-left: 4px solid #D97706; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Application ID:</strong> {application['application_id']}</p>
                        <p style="margin: 5px 0;"><strong>Visa Type:</strong> {application['visa_type'].title()}</p>
                        <p style="margin: 5px 0;"><strong>Travel Dates:</strong> {application['travel_details']['arrival_date']} to {application['travel_details']['departure_date']}</p>
                    </div>
                    
                    <p style="font-size: 14px; margin-bottom: 15px;">Please find your official e-Visa document attached to this email. Print a copy and present it at immigration upon arrival.</p>
                    
                    <div style="background-color: #fef3c7; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 13px; color: #92400e;"><strong>⚠️ Important:</strong> Visa fee payment will be collected at the port of entry. Please have payment ready in cash or card.</p>
                    </div>
                    
                    <p style="font-size: 14px; margin-top: 20px;">We look forward to welcoming you to Meowls!</p>
                    
                    <p style="font-size: 13px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        Best regards,<br>
                        <strong>Immigration Department</strong><br>
                        Republic of Meowls
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params_base = {
            "from": SENDER_EMAIL,
            "subject": "Your Meowls Visa is APPROVED!",
            "html": html_content,
            "attachments": [{
                "filename": f"meowls_visa_{application['application_id']}.pdf",
                "content": pdf_bytes
            }]
        }

        successes, failures = [], []
        for idx, recipient in enumerate(all_recipients):
            try:
                params = {**params_base, "to": [recipient]}
                await asyncio.to_thread(resend.Emails.send, params)
                successes.append(recipient)
            except Exception as send_err:
                failures.append({"email": recipient, "error": str(send_err)})
                logger.error(f"Approval email to {recipient} failed: {send_err}")
            # Respect Resend 5 req/sec limit
            if idx < len(all_recipients) - 1:
                await asyncio.sleep(0.25)

        logger.info(
            f"Approval email results — success: {successes}, failures: {failures}"
        )
        return len(successes) > 0
    except Exception as e:
        logger.error(f"Failed to send approval email: {str(e)}")
        return False

async def send_rejection_email(application: dict, notes: str = ""):
    """Send kind visa rejection email. Sends individually per recipient."""
    try:
        # Get all admin emails to include in recipients
        admin_users = await db.users.find({"role": "admin"}, {"_id": 0, "email": 1}).to_list(100)
        admin_emails = [admin["email"] for admin in admin_users]
        
        applicant_email = application['personal_info']['email']
        all_recipients = []
        for e in [applicant_email] + admin_emails:
            if e and e not in all_recipients:
                all_recipients.append(e)
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #0F172A; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">Visa Application Update</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; color: #D97706;">Republic of Meowls Immigration</p>
                </div>
                
                <div style="background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{application['personal_info']['full_name']}</strong>,</p>
                    
                    <p style="font-size: 14px; margin-bottom: 15px;">Thank you for your interest in visiting the Republic of Meowls. We have carefully reviewed your visa application (ID: <strong>{application['application_id']}</strong>).</p>
                    
                    <div style="background-color: #fee2e2; padding: 20px; border-left: 4px solid #dc2626; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; font-size: 14px; color: #991b1b;">Unfortunately, we are unable to approve your visa application at this time.</p>
                    </div>
                    
                    {f'<div style="background-color: white; padding: 15px; border-radius: 6px; margin: 20px 0;"><p style="margin: 0; font-size: 13px;"><strong>Reason:</strong> {notes}</p></div>' if notes else ''}
                    
                    <p style="font-size: 14px; margin-bottom: 15px;">We understand this may be disappointing news. However, we encourage you to:</p>
                    
                    <ul style="font-size: 14px; margin-bottom: 15px;">
                        <li>Review the requirements for your visa category</li>
                        <li>Ensure all documentation is complete and accurate</li>
                        <li>Consider reapplying once any issues have been addressed</li>
                    </ul>
                    
                    <div style="background-color: #dbeafe; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 13px; color: #1e40af;"><strong>ℹ️ Need Help?</strong> Contact our visa support team at visa@meowls.gov for guidance on your next steps.</p>
                    </div>
                    
                    <p style="font-size: 14px; margin-top: 20px;">We appreciate your understanding and hope to welcome you to Meowls in the future.</p>
                    
                    <p style="font-size: 13px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        Best regards,<br>
                        <strong>Immigration Department</strong><br>
                        Republic of Meowls
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        params_base = {
            "from": SENDER_EMAIL,
            "subject": "Meowls Visa Application Update",
            "html": html_content
        }

        successes, failures = [], []
        for idx, recipient in enumerate(all_recipients):
            try:
                params = {**params_base, "to": [recipient]}
                await asyncio.to_thread(resend.Emails.send, params)
                successes.append(recipient)
            except Exception as send_err:
                failures.append({"email": recipient, "error": str(send_err)})
                logger.error(f"Rejection email to {recipient} failed: {send_err}")
            # Respect Resend 5 req/sec limit
            if idx < len(all_recipients) - 1:
                await asyncio.sleep(0.25)

        logger.info(
            f"Rejection email results — success: {successes}, failures: {failures}"
        )
        return len(successes) > 0
    except Exception as e:
        logger.error(f"Failed to send rejection email: {str(e)}")
        return False

@api_router.post("/auth/register")
async def register(user_data: UserRegister, response: Response):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    password_hash = hash_password(user_data.password)
    
    user = {
        "user_id": user_id,
        "email": user_data.email,
        "password_hash": password_hash,
        "name": user_data.name,
        "picture": None,
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    session_token = f"session_{uuid.uuid4().hex}"
    session = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    user_copy = user.copy()
    user_copy.pop('password_hash', None)
    user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
    return User(**user_copy)

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_token = f"session_{uuid.uuid4().hex}"
    session = {
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    user_copy = user_doc.copy()
    user_copy.pop('password_hash', None)
    if isinstance(user_copy['created_at'], str):
        user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
    return User(**user_copy)

@api_router.post("/auth/session")
async def process_google_session(session_data: SessionData, response: Response):
    try:
        ext_response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_data.session_id},
            timeout=10
        )
        ext_response.raise_for_status()
        data = ext_response.json()
        
        user_doc = await db.users.find_one({"email": data["email"]}, {"_id": 0})
        
        if user_doc:
            user_id = user_doc["user_id"]
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "name": data["name"],
                    "picture": data["picture"]
                }}
            )
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user = {
                "user_id": user_id,
                "email": data["email"],
                "name": data["name"],
                "picture": data["picture"],
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user)
        
        session_token = data["session_token"]
        session = {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_sessions.insert_one(session)
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7*24*60*60
        )
        
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        user_copy = user_doc.copy()
        user_copy.pop('password_hash', None)
        if isinstance(user_copy['created_at'], str):
            user_copy['created_at'] = datetime.fromisoformat(user_copy['created_at'])
        return User(**user_copy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/auth/me")
async def get_me(request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, session_token: Optional[str] = Cookie(None)):
    token = session_token
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@api_router.post("/applications")
async def create_application(app_data: ApplicationCreate, request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    application_id = f"app_{uuid.uuid4().hex[:12]}"
    application = {
        "application_id": application_id,
        "user_id": user.user_id,
        "visa_type": app_data.visa_type,
        "status": "draft",
        "personal_info": app_data.personal_info,
        "travel_details": app_data.travel_details,
        "documents": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.visa_applications.insert_one(application)
    
    app_copy = application.copy()
    app_copy['created_at'] = datetime.fromisoformat(app_copy['created_at'])
    app_copy['updated_at'] = datetime.fromisoformat(app_copy['updated_at'])
    return VisaApplication(**app_copy)

@api_router.get("/applications")
async def get_applications(request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    apps = await db.visa_applications.find({"user_id": user.user_id}, {"_id": 0}).to_list(1000)
    
    for app in apps:
        if isinstance(app['created_at'], str):
            app['created_at'] = datetime.fromisoformat(app['created_at'])
        if isinstance(app['updated_at'], str):
            app['updated_at'] = datetime.fromisoformat(app['updated_at'])
    
    return [VisaApplication(**app) for app in apps]

@api_router.get("/applications/{application_id}")
async def get_application(application_id: str, request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app["user_id"] != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(app['created_at'], str):
        app['created_at'] = datetime.fromisoformat(app['created_at'])
    if isinstance(app['updated_at'], str):
        app['updated_at'] = datetime.fromisoformat(app['updated_at'])
    
    return VisaApplication(**app)

@api_router.put("/applications/{application_id}")
async def update_application(application_id: str, app_data: ApplicationCreate, request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
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
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if isinstance(updated_app['created_at'], str):
        updated_app['created_at'] = datetime.fromisoformat(updated_app['created_at'])
    if isinstance(updated_app['updated_at'], str):
        updated_app['updated_at'] = datetime.fromisoformat(updated_app['updated_at'])
    
    return VisaApplication(**updated_app)

@api_router.post("/applications/{application_id}/documents")
async def upload_document(application_id: str, file: UploadFile = File(...), doc_type: str = "passport", request: Request = None, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    content = await file.read()
    encoded = base64.b64encode(content).decode('utf-8')
    
    document_data = {
        "filename": file.filename,
        "content_type": file.content_type,
        "data": encoded
    }
    
    await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": {
            f"documents.{doc_type}": document_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Document uploaded successfully", "doc_type": doc_type}

@api_router.post("/applications/{application_id}/submit")
async def submit_application(application_id: str, request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "status": "submitted",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Application submitted successfully"}

@api_router.get("/admin/applications")
async def get_all_applications(request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    apps = await db.visa_applications.find({}, {"_id": 0}).to_list(1000)
    
    for app in apps:
        if isinstance(app['created_at'], str):
            app['created_at'] = datetime.fromisoformat(app['created_at'])
        if isinstance(app['updated_at'], str):
            app['updated_at'] = datetime.fromisoformat(app['updated_at'])
    
    return [VisaApplication(**app) for app in apps]

@api_router.put("/admin/applications/{application_id}/status")
async def update_application_status(application_id: str, status_data: StatusUpdate, request: Request, session_token: Optional[str] = Cookie(None)):
    user = await get_current_user(request, session_token)
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": status_data.status,
        "updated_at": now_iso,
        "status_changed_at": now_iso,
        "status_seen_at": None,  # reset on every status change so applicant gets new notification
    }
    
    if status_data.notes:
        update_data["admin_notes"] = status_data.notes

    # If approved, generate the PDF now and persist it so the applicant can download in-app
    if status_data.status == "approved":
        try:
            visa_content = await generate_visa_document_with_ai(app)
            pdf_buffer = create_visa_pdf(visa_content, app)
            pdf_b64 = base64.b64encode(pdf_buffer.getvalue()).decode("ascii")
            update_data["visa_document"] = {
                "filename": f"meowls_visa_{application_id}.pdf",
                "content_type": "application/pdf",
                "data": pdf_b64,
                "generated_at": now_iso,
            }
        except Exception as e:
            logger.error(f"Failed to pre-generate visa PDF for {application_id}: {e}")
    
    result = await db.visa_applications.update_one(
        {"application_id": application_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    updated_app = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    
    if status_data.status == "approved":
        asyncio.create_task(send_approval_email(updated_app))
        asyncio.create_task(send_push_to_user(updated_app["user_id"], {
            "title": "Meowls Visa Approved",
            "body": f"Your {updated_app['visa_type'].title()} visa has been approved. Tap to download your visa PDF.",
            "application_id": application_id,
            "status": "approved",
        }))
    elif status_data.status == "rejected":
        asyncio.create_task(send_rejection_email(updated_app, status_data.notes or ""))
        asyncio.create_task(send_push_to_user(updated_app["user_id"], {
            "title": "Meowls Visa Update",
            "body": f"Your visa application ({application_id}) was not approved. Tap to see details.",
            "application_id": application_id,
            "status": "rejected",
        }))
    
    return {"message": "Status updated successfully", "email_sent": status_data.status in ["approved", "rejected"]}

# ============================================================
# Web Push + In-app Notifications
# ============================================================

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

async def send_push_to_user(user_id: str, payload: dict):
    """Send a web push notification to every subscription registered for this user."""
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not configured; skipping push")
        return
    subs = await db.push_subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    if not subs:
        logger.info(f"No push subscriptions for user {user_id}")
        return

    successes, dead = 0, []
    for sub in subs:
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=json_lib.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_SUB},
            )
            successes += 1
        except WebPushException as e:
            # 404/410 means the subscription is no longer valid — remove it
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (404, 410):
                dead.append(sub["endpoint"])
            logger.error(f"Push to {sub['endpoint'][:60]}... failed: {e}")
        except Exception as e:
            logger.error(f"Push error: {e}")
    if dead:
        await db.push_subscriptions.delete_many({"endpoint": {"$in": dead}})
    logger.info(f"Push sent to user {user_id}: {successes}/{len(subs)} delivered, {len(dead)} pruned")


@api_router.get("/push/vapid-public-key")
async def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return {"public_key": VAPID_PUBLIC_KEY}


@api_router.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    request: Request,
    session_token: Optional[str] = Cookie(None),
):
    user = await get_current_user(request, session_token)
    doc = {
        "user_id": user.user_id,
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": doc},
        upsert=True,
    )
    return {"ok": True}


@api_router.post("/push/unsubscribe")
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


@api_router.get("/notifications")
async def get_notifications(request: Request, session_token: Optional[str] = Cookie(None)):
    """Return all the user's applications whose status was changed and not yet seen."""
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


@api_router.post("/notifications/{application_id}/read")
async def mark_notification_read(
    application_id: str, request: Request, session_token: Optional[str] = Cookie(None)
):
    user = await get_current_user(request, session_token)
    result = await db.visa_applications.update_one(
        {"application_id": application_id, "user_id": user.user_id},
        {"$set": {"status_seen_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"ok": True}


@api_router.get("/applications/{application_id}/visa-pdf")
async def download_visa_pdf(
    application_id: str, request: Request, session_token: Optional[str] = Cookie(None)
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
        # Generate on-demand if missing (e.g. applications approved before this feature)
        try:
            visa_content = await generate_visa_document_with_ai(app_doc)
            pdf_buffer = create_visa_pdf(visa_content, app_doc)
            pdf_bytes = pdf_buffer.getvalue()
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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()