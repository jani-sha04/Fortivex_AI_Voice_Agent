"""
Knowledge Base API routes
"""

import os
import logging
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.knowledge import KnowledgeDocument
from app.schemas.schemas import DocumentResponse
from app.services.rag_service import rag_service, extract_text_from_file
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])

UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"application/pdf", "text/plain"}
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF or TXT document to the knowledge base."""
    # Validate file extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF and TXT files are supported. Got: {ext}",
        )

    file_type = ext.lstrip(".")

    # Read and validate size
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Save file
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{filename}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as f:
        f.write(data)

    # Create DB record
    doc = KnowledgeDocument(
        id=doc_id,
        filename=safe_name,
        original_name=filename,
        file_type=file_type,
        file_size=len(data),
        status="processing",
    )
    db.add(doc)
    db.commit()

    # Process in background
    background_tasks.add_task(
        process_document,
        doc_id=doc_id,
        file_path=str(file_path),
        filename=filename,
        file_type=file_type,
        db=db,
    )

    db.refresh(doc)
    return doc


def process_document(doc_id: str, file_path: str, filename: str, file_type: str, db: Session):
    """Background task: extract text, embed, and store in ChromaDB."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return

    try:
        text = extract_text_from_file(file_path, file_type)
        if not text.strip():
            doc.status = "error"
            doc.error_message = "No text could be extracted from the file."
            db.commit()
            return

        chunk_count = rag_service.add_document(doc_id, text, filename, file_type)
        doc.chunk_count = chunk_count
        doc.status = "ready"

    except Exception as e:
        logger.error(f"Document processing error: {e}")
        doc.status = "error"
        doc.error_message = str(e)

    from datetime import datetime, timezone
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded knowledge documents."""
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()
    return docs


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and remove its embeddings from ChromaDB."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from ChromaDB
    rag_service.delete_document(document_id)

    # Remove file
    file_path = UPLOAD_DIR / doc.filename
    if file_path.exists():
        file_path.unlink()

    db.delete(doc)
    db.commit()

    return {"success": True, "message": f"Document '{doc.original_name}' deleted."}
