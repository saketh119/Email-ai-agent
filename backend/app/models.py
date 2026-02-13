from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base

# Stores dynamic prompts
class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Stores processed emails
class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    category = Column(String)
    reply = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Tracks OpenAI token usage (Production-level feature)
class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
