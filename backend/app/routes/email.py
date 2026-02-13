from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from ..models import Email, Prompt, UsageLog
from ..services.gemini_service import process_email_with_gemini

router = APIRouter()


# ---------- Request Schema (Production) ----------
class EmailRequest(BaseModel):
    email_text: str


# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- API Endpoint ----------
@router.post("/process-email")
def process_email(request: EmailRequest, db: Session = Depends(get_db)):

    email_text = request.email_text

    # Get dynamic prompt
    prompt = db.query(Prompt).filter(Prompt.name == "email_assistant").first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found in database")

    # Call Gemini
    category, reply, tokens = process_email_with_gemini(prompt.content, email_text)

    # Save email record
    email_record = Email(
        content=email_text,
        category=category,
        reply=reply
    )
    db.add(email_record)

    # Save usage log
    usage = UsageLog(
        endpoint="process-email",
        tokens_used=tokens
    )
    db.add(usage)

    db.commit()

    # Clean production response
    return {
        "category": category,
        "reply": reply,
        "tokens_used": tokens
    }
