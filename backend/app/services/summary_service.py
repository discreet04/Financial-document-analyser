import json
import logging
import re
from functools import lru_cache

from fastapi import HTTPException, status
from langchain_ollama import ChatOllama
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.chat import Citation
from app.schemas.summary import ExecutiveSummary


logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _ollama_summary_model(
    model: str,
    base_url: str,
    keep_alive: str,
    num_ctx: int,
    num_predict: int,
) -> ChatOllama:
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0,
        format="json",
        keep_alive=keep_alive,
        num_ctx=num_ctx,
        num_predict=num_predict,
    )


def _chat_model() -> ChatOllama:
    settings = get_settings()
    if settings.llm_provider.strip().lower() != "ollama":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unsupported LLM_PROVIDER '{settings.llm_provider}'",
        )
    return _ollama_summary_model(
        settings.ollama_model,
        settings.ollama_base_url,
        settings.ollama_keep_alive,
        settings.ollama_num_ctx,
        settings.ollama_summary_num_predict,
    )


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def _matches_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _pick_sentences(sentences: list[str], keywords: tuple[str, ...], limit: int) -> list[str]:
    matches = [sentence for sentence in sentences if _matches_any(sentence, keywords)]
    return matches[:limit]


def _local_summary(document: Document, chunks: list[DocumentChunk], citations: list[Citation]) -> ExecutiveSummary:
    text = " ".join(chunk.chunk_text for chunk in chunks)
    sentences = _sentences(text)
    preview = " ".join(sentences[:4]) if sentences else text[:800]

    risk_keywords = ("risk", "liability", "penalty", "default", "breach", "terminate", "loss", "debt", "obligation")
    finance_keywords = ("revenue", "income", "cash", "asset", "liability", "profit", "loss", "expense", "$", "%", "amount")
    compliance_keywords = ("compliance", "regulation", "policy", "audit", "tax", "legal", "law", "required", "must", "shall")

    key_risks = _pick_sentences(sentences, risk_keywords, 5)
    financial_highlights = _pick_sentences(sentences, finance_keywords, 5)
    compliance_concerns = _pick_sentences(sentences, compliance_keywords, 5)
    important_findings = sentences[:5]

    return ExecutiveSummary(
        executive_summary=(
            f"Local summary for {document.filename}. "
            f"{preview or 'The document text was extracted, but there was not enough sentence structure for a detailed summary.'}"
        ),
        key_risks=key_risks or ["No explicit risk statements were detected in the extracted text."],
        financial_highlights=financial_highlights or ["No clear financial figures or highlights were detected in the extracted text."],
        compliance_concerns=compliance_concerns or ["No explicit compliance concerns were detected in the extracted text."],
        important_findings=important_findings or ["No important findings could be extracted from the available text."],
        citations=citations,
    )


def generate_summary(db: Session, user: User, document_id: int) -> ExecutiveSummary:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id, DocumentChunk.user_id == user.id)
            .order_by(DocumentChunk.page_number, DocumentChunk.chunk_index)
        )
    )
    if not chunks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No processed chunks found for this document")

    citations = [
        Citation(
            document_id=document.id,
            document_name=document.filename,
            page_number=chunk.page_number,
            chunk_id=chunk.id,
            chunk_text=chunk.chunk_text,
        )
        for chunk in chunks[: get_settings().summary_citation_limit]
    ]

    context_parts = []
    remaining_chars = get_settings().summary_context_chars
    for chunk in chunks:
        block = f"[Page {chunk.page_number}, Chunk {chunk.id}]\n{chunk.chunk_text}"
        if remaining_chars - len(block) < 0:
            break
        context_parts.append(block)
        remaining_chars -= len(block)

    prompt = f"""
You are a senior fintech analyst. Use only the document context below.
Return valid JSON with these exact keys:
executive_summary, key_risks, financial_highlights, compliance_concerns, important_findings.
Each key except executive_summary must be an array of concise strings.
If evidence is missing, state that clearly instead of guessing.

Document: {document.filename}

Context:
{chr(10).join(context_parts)}
""".strip()

    try:
        response = _chat_model().invoke(prompt)
        content = str(response.content).strip()
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        parsed = json.loads(content)
    except Exception as exc:
        logger.exception("Ollama summary generation failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama summary generation failed: {str(exc)}",
        ) from exc

    return ExecutiveSummary(
        executive_summary=str(parsed.get("executive_summary", "")),
        key_risks=list(parsed.get("key_risks", [])),
        financial_highlights=list(parsed.get("financial_highlights", [])),
        compliance_concerns=list(parsed.get("compliance_concerns", [])),
        important_findings=list(parsed.get("important_findings", [])),
        citations=citations,
    )
