from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from ..models import Email, Prompt, UsageLog

from ..services.gemini_service import process_email_with_gemini
from ..services.gmail_service import (
    get_latest_emails,
    get_gmail_service,
    create_draft
)
from ..services.gmail_service import (
    get_unread_emails,
    get_or_create_label,
    add_label_to_email
)

router = APIRouter()


# ---------- Request Schema ----------
class EmailRequest(BaseModel):
    email_text: str


# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================
# 1. Process Manual Email (Frontend API)
# =====================================================
@router.post("/process-email")
def process_email(request: EmailRequest, db: Session = Depends(get_db)):

    prompt = db.query(Prompt).filter(Prompt.name == "email_assistant").first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    category, reply, tokens = process_email_with_gemini(
        prompt.content,
        request.email_text
    )

    # Save email
    email_record = Email(
        content=request.email_text,
        category=category,
        reply=reply
    )
    db.add(email_record)

    # Log usage
    usage = UsageLog(
        endpoint="process-email",
        tokens_used=tokens
    )
    db.add(usage)

    db.commit()

    return {
        "category": category,
        "reply": reply,
        "tokens_used": tokens
    }


# =====================================================
# 2. Fetch Latest Gmail Emails
# =====================================================
@router.get("/fetch-gmail")
def fetch_gmail():
    emails = get_latest_emails(max_results=5)
    return {"emails": emails}


# =====================================================
# 3. Process Gmail Emails (AI only)
# =====================================================
@router.get("/process-gmail")
def process_gmail(db: Session = Depends(get_db)):

    prompt = db.query(Prompt).filter(Prompt.name == "email_assistant").first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    emails = get_latest_emails(max_results=5)

    processed_emails = []

    for email in emails:
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"

        category, reply, tokens = process_email_with_gemini(
            prompt.content,
            email_text
        )

        # Save to DB
        db.add(Email(
            content=email_text,
            category=category,
            reply=reply
        ))

        db.add(UsageLog(
            endpoint="process-gmail",
            tokens_used=tokens
        ))

        processed_emails.append({
            "subject": email["subject"],
            "category": category,
            "reply": reply
        })

    db.commit()

    return {"processed_emails": processed_emails}


# =====================================================
# 4. Process Gmail + Create Draft Replies (FULL AI COPILOT)
# =====================================================
@router.get("/process-gmail-drafts")
def process_gmail_drafts(db: Session = Depends(get_db)):

    prompt = db.query(Prompt).filter(Prompt.name == "email_assistant").first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    service = get_gmail_service()
    emails = get_latest_emails(max_results=3)

    results = []

    for email in emails:
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"

        category, reply, tokens = process_email_with_gemini(
            prompt.content,
            email_text
        )

        # Create Gmail draft
        draft = create_draft(
            service=service,
            to=email["sender"],
            subject=email["subject"],
            message_text=reply
        )

        # Save to DB
        db.add(Email(
            content=email_text,
            category=category,
            reply=reply
        ))

        db.add(UsageLog(
            endpoint="process-gmail-drafts",
            tokens_used=tokens
        ))

        results.append({
            "subject": email["subject"],
            "category": category,
            "draft_id": draft["id"]
        })

    db.commit()

    return {"drafts_created": results}


# =====================================================
# 5. Process Unread Emails (FULL AI COPILOT)
# =====================================================
@router.get("/process-unread")
def process_unread_emails(db: Session = Depends(get_db)):

    prompt = db.query(Prompt).filter(Prompt.name == "email_assistant").first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    service = get_gmail_service()

    # Get label
    label_id = get_or_create_label(service, "AI-Processed")

    # Fetch unread emails
    emails = get_unread_emails(max_results=5)

    results = []

    for email in emails:
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"

        category, reply, tokens = process_email_with_gemini(
            prompt.content,
            email_text
        )

        # Create draft
        draft = create_draft(
            service=service,
            to=email["sender"],
            subject=email["subject"],
            message_text=reply
        )

        # Add label and mark as read
        add_label_to_email(service, email["id"], label_id)

        # Save to DB
        db.add(Email(
            content=email_text,
            category=category,
            reply=reply
        ))

        db.add(UsageLog(
            endpoint="process-unread",
            tokens_used=tokens
        ))

        results.append({
            "subject": email["subject"],
            "category": category,
            "draft_id": draft["id"]
        })

    db.commit()

    return {"processed_unread_emails": results}
