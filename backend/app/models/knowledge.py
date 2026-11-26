"""
Knowledge document model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from app.database.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(300), nullable=False)
    original_name = Column(String(300), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, txt
    file_size = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")  # processing, ready, error
    error_message = Column(Text, nullable=True)
    chroma_collection = Column(String(100), default="fortivex_knowledge")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
