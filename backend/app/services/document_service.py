import logging
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.pdf_service import extract_pdf_chunks
from app.services.vector_store import add_chunks_to_index, rebuild_user_index


logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
COPY_CHUNK_SIZE = 1024 * 1024


def _ensure_pdf(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")


def _ensure_pdf_header(file: UploadFile) -> None:
    header = file.file.read(len(PDF_SIGNATURE))
    file.file.seek(0)
    if header != PDF_SIGNATURE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF")


def _save_upload(file: UploadFile, storage_path: Path) -> None:
    bytes_written = 0

    with storage_path.open("wb") as buffer:
        while chunk := file.file.read(COPY_CHUNK_SIZE):
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="PDF file size must be 20 MB or smaller",
                )
            buffer.write(chunk)

    if bytes_written == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")


def _extract_pdf_chunks(storage_path: Path):
    try:
        return extract_pdf_chunks(str(storage_path))
    except Exception as exc:
        logger.exception("PDF text extraction failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF text extraction failed: {str(exc)}",
        ) from exc


def _add_chunks_to_index(user_id: int, chunks: list[DocumentChunk], filename: str) -> None:
    try:
        add_chunks_to_index(user_id, chunks, filename)
    except HTTPException as exc:
        logger.exception("Embedding generation failed")
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Embedding generation failed: {detail}",
        ) from exc
    except Exception as exc:
        logger.exception("Embedding generation failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Embedding generation failed: {str(exc)}",
        ) from exc


def upload_document(db: Session, user: User, file: UploadFile) -> Document:
    _ensure_pdf(file)
    _ensure_pdf_header(file)
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    stored_name = f"{user.id}_{uuid4().hex}_{safe_name}"
    storage_path = upload_dir / stored_name

    try:
        _save_upload(file, storage_path)

        page_chunks = _extract_pdf_chunks(storage_path)
        if not page_chunks:
            storage_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No extractable text was found in this PDF. Scanned, image-only, or encrypted PDFs need OCR or unlocking before upload.",
            )

        document = Document(user_id=user.id, filename=safe_name, storage_path=str(storage_path))
        db.add(document)
        db.flush()

        chunk_models = [
            DocumentChunk(
                document_id=document.id,
                user_id=user.id,
                page_number=chunk.page_number,
                chunk_index=index,
                chunk_text=chunk.text,
            )
            for index, chunk in enumerate(page_chunks)
        ]
        db.add_all(chunk_models)
        db.flush()

        _add_chunks_to_index(user.id, chunk_models, document.filename)
        db.commit()
        db.refresh(document)
        return document
    except HTTPException:
        db.rollback()
        storage_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        storage_path.unlink(missing_ok=True)
        logger.exception("Document upload failed")
        detail = "Document upload failed"
        if settings.environment == "development":
            detail = f"{detail}: {str(exc)}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc


def list_documents(db: Session, user: User) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.upload_date.desc())))


def delete_document(db: Session, user: User, document_id: int) -> None:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    storage_path = Path(document.storage_path)
    db.delete(document)
    db.commit()
    storage_path.unlink(missing_ok=True)
    rebuild_user_index(db, user.id)
