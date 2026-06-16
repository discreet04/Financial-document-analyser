import logging
import shutil
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangChainDocument
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


logger = logging.getLogger(__name__)


def _embedding_provider() -> str:
    return get_settings().embedding_provider.strip().lower()


@lru_cache(maxsize=4)
def _huggingface_embedding_model(model_name: str) -> HuggingFaceEmbeddings:
    logger.info("Loading Hugging Face embedding model: %s", model_name)
    return HuggingFaceEmbeddings(model_name=model_name)


def _embedding_model() -> Embeddings:
    settings = get_settings()
    provider = _embedding_provider()

    if provider == "huggingface":
        return _huggingface_embedding_model(settings.huggingface_embedding_model)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported EMBEDDING_PROVIDER '{settings.embedding_provider}'",
    )


def vector_index_enabled() -> bool:
    provider = _embedding_provider()
    if provider == "huggingface":
        return True
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported EMBEDDING_PROVIDER '{get_settings().embedding_provider}'",
    )


def _embedding_index_name() -> str:
    settings = get_settings()
    provider = _embedding_provider()
    model_name = settings.huggingface_embedding_model
    safe_model_name = "".join(char if char.isalnum() else "_" for char in model_name).strip("_").lower()
    return f"{provider}_{safe_model_name}"


def _user_index_path(user_id: int) -> Path:
    settings = get_settings()
    return Path(settings.vector_store_dir) / _embedding_index_name() / f"user_{user_id}"


def _to_langchain_document(chunk: DocumentChunk, document_name: str) -> LangChainDocument:
    return LangChainDocument(
        page_content=chunk.chunk_text,
        metadata={
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_name": document_name,
            "page_number": chunk.page_number,
        },
    )


def load_user_index(user_id: int) -> FAISS | None:
    if not vector_index_enabled():
        return None

    index_path = _user_index_path(user_id)
    if not index_path.exists():
        return None
    if not (index_path / "index.faiss").exists() or not (index_path / "index.pkl").exists():
        logger.warning("Incomplete FAISS index for user %s at %s; rebuilding from document chunks", user_id, index_path)
        shutil.rmtree(index_path, ignore_errors=True)
        return None

    try:
        return FAISS.load_local(
            str(index_path),
            _embedding_model(),
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        logger.exception("Failed to load FAISS index for user %s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Vector index could not be loaded") from exc


def add_chunks_to_index(user_id: int, chunks: list[DocumentChunk], document_name: str) -> None:
    if not chunks:
        return
    settings = get_settings()
    if not vector_index_enabled():
        logger.info("Vector index is disabled for user %s", user_id)
        return

    index_path = _user_index_path(user_id)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    documents = [_to_langchain_document(chunk, document_name) for chunk in chunks]
    embeddings = _embedding_model()

    try:
        index = load_user_index(user_id)
        if index is None:
            index = FAISS.from_documents(documents, embeddings)
        else:
            index.add_documents(documents)
        index.save_local(str(index_path))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to update FAISS index for user %s", user_id)
        detail = "Vector index could not be updated"
        if settings.environment == "development":
            detail = f"{detail}: {str(exc)}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


def rebuild_user_index(db: Session, user_id: int) -> None:
    index_path = _user_index_path(user_id)
    if index_path.exists():
        shutil.rmtree(index_path)
    if not vector_index_enabled():
        logger.info("Vector index rebuild is disabled for user %s", user_id)
        return

    rows = db.execute(
        select(DocumentChunk, Document.filename)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.user_id == user_id)
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
    ).all()

    documents = [_to_langchain_document(chunk, filename) for chunk, filename in rows]
    if not documents:
        return

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index = FAISS.from_documents(documents, _embedding_model())
    index.save_local(str(index_path))
