"""AI document generation + PDF rendering for approved visas."""
import base64
import logging
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from emergentintegrations.llm.chat import LlmChat, UserMessage

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


async def generate_visa_document_with_ai(application: dict) -> str:
    """Generate the free-text body of a visa approval letter via OpenAI."""
    try:
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"visa_{application['application_id']}",
            system_message=(
                "You are an official document generator for the Republic of Meowls "
                "Immigration Department. Generate formal, professional visa documents."
            ),
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

        return await chat.send_message(user_message)
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
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
    """Render the visa PDF with the applicant's photo embedded."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=24,
        textColor=colors.HexColor('#0F172A'), spaceAfter=30,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
    )
    header_style = ParagraphStyle(
        'Header', parent=styles['Normal'], fontSize=16,
        textColor=colors.HexColor('#D97706'), spaceAfter=20,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontSize=11,
        textColor=colors.HexColor('#334155'), spaceAfter=12,
        alignment=TA_LEFT, fontName='Helvetica',
    )

    story = [
        Paragraph("REPUBLIC OF MEOWLS", title_style),
        Paragraph("Official e-Visa Document", header_style),
        Spacer(1, 0.3 * inch),
    ]

    # Embed applicant photo if available
    try:
        photo_data = application.get('documents', {}).get('photo')
        if isinstance(photo_data, dict) and 'data' in photo_data:
            photo_bytes = base64.b64decode(photo_data['data'])
            img = RLImage(BytesIO(photo_bytes), width=1.5 * inch, height=1.5 * inch)
            photo_table = Table([[img]], colWidths=[1.5 * inch])
            photo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0F172A')),
            ]))
            story.append(photo_table)
            story.append(Spacer(1, 0.2 * inch))
    except Exception as e:
        logger.error(f"Failed to add photo to PDF: {e}")

    for line in content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 0.5 * inch))

    data = [
        ['Application ID:', application['application_id']],
        ['Issue Date:', datetime.now(timezone.utc).strftime('%B %d, %Y')],
        ['Status:', 'APPROVED'],
    ]
    table = Table(data, colWidths=[2 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer


async def build_and_persist_visa_pdf(application_id: str) -> None:
    """Background task: generate the AI text + PDF and persist base64 on the application."""
    from database import db  # local import to avoid cycles
    app_doc = await db.visa_applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app_doc:
        logger.error(f"build_and_persist_visa_pdf: application {application_id} not found")
        return
    try:
        content = await generate_visa_document_with_ai(app_doc)
        pdf_buffer = create_visa_pdf(content, app_doc)
        pdf_b64 = base64.b64encode(pdf_buffer.getvalue()).decode("ascii")
        await db.visa_applications.update_one(
            {"application_id": application_id},
            {"$set": {"visa_document": {
                "filename": f"meowls_visa_{application_id}.pdf",
                "content_type": "application/pdf",
                "data": pdf_b64,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }}},
        )
        logger.info(f"Visa PDF generated + persisted for {application_id}")
    except Exception as e:
        logger.error(f"build_and_persist_visa_pdf failed for {application_id}: {e}")
