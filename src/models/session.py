from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from src.core.client import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    conversation_id = Column(String, primary_key=True)
    history = Column(JSONB, default=list, server_default="[]")
    preferences = Column(JSONB, default=dict, server_default="{}")
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
