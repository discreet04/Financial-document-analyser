import logging
import re
from collections import Counter
from functools import lru_cache

from fastapi import HTTPException, status
from langchain_ollama import ChatOllama
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chat_history import ChatHistory
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.chat import ChatResponse, Citation
from app.services.vector_store import load_user_index


logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _ollama_chat_model(
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
    return _ollama_chat_model(
        settings.ollama_model,
        settings.ollama_base_url,
        settings.ollama_keep_alive,
        settings.ollama_num_ctx,
        settings.ollama_chat_num_predict,
    )


def _llm_enabled() -> bool:
    return get_settings().llm_provider.strip().lower() == "ollama"


def _format_context(citations: list[Citation]) -> str:
    sections = []
    for index, citation in enumerate(citations, start=1):
        sections.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Document: {citation.document_name}",
                    f"Page: {citation.page_number}",
                    f"Chunk ID: {citation.chunk_id}",
                    citation.chunk_text,
                ]
            )
        )
    return "\n\n".join(sections)


def _terms(text: str) -> list[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "with",
    }
    return [term for term in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(term) > 2 and term not in stopwords]


def _local_search(db: Session, user: User, question: str, k: int) -> list[Citation]:
    query_terms = Counter(_terms(question))
    if not query_terms:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ask a more specific question")

    rows = db.execute(
        select(DocumentChunk, Document.filename)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.user_id == user.id)
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
    ).all()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload documents before asking questions")

    scored: list[tuple[float, DocumentChunk, str]] = []
    for chunk, filename in rows:
        chunk_terms = Counter(_terms(chunk.chunk_text))
        score = sum(query_terms[term] * chunk_terms.get(term, 0) for term in query_terms)
        if score:
            scored.append((float(score), chunk, filename))

    if not scored:
        lower_question = question.lower()
        scored = [
            (1.0, chunk, filename)
            for chunk, filename in rows
            if any(word in chunk.chunk_text.lower() for word in lower_question.split())
        ]

    if not scored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant document context was found")

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        Citation(
            document_id=chunk.document_id,
            document_name=filename,
            page_number=chunk.page_number,
            chunk_id=chunk.id,
            chunk_text=chunk.chunk_text,
            score=score,
        )
        for score, chunk, filename in scored[:k]
    ]


def _local_answer(question: str, citations: list[Citation]) -> str:
    context = " ".join(citation.chunk_text for citation in citations)
    sentences = re.split(r"(?<=[.!?])\s+", context)
    query_terms = set(_terms(question))
    ranked = sorted(
        (sentence.strip() for sentence in sentences if sentence.strip()),
        key=lambda sentence: sum(1 for term in query_terms if term in sentence.lower()),
        reverse=True,
    )
    best_sentences = [sentence for sentence in ranked[:3] if any(term in sentence.lower() for term in query_terms)]
    if not best_sentences:
        best_sentences = [citations[0].chunk_text[:700].strip()]

    source_names = sorted({citation.document_name for citation in citations})
    answer = " ".join(best_sentences)
    return (
        f"Based on the uploaded document context, {answer}\n\n"
        f"Sources used: {', '.join(source_names)}. "
        "For a more polished answer, start Ollama and make sure the configured model is available."
    )


def answer_question(db: Session, user: User, question: str, top_k: int | None = None,document_id: int | None = None) -> ChatResponse:
    settings = get_settings()
    k = top_k or settings.rag_top_k
    index = load_user_index(user.id)

    if index is None:
        citations = _local_search(db, user, question, k)
    else:
        try:     
            raw_results = index.similarity_search_with_score(
                question,
                k=50
    )
            if document_id is not None:
                raw_results = [
                    (doc, score)
                    for doc, score in raw_results
                    if int(doc.metadata.get("document_id", 0))
                    == document_id
                    ]
                results = raw_results[:k]
        except Exception as exc:
            logger.exception("Similarity search failed")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Retrieval failed") from exc

        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No relevant document context was found")

        citations = [
            Citation(
                document_id=int(doc.metadata["document_id"]),
                document_name=str(doc.metadata["document_name"]),
                page_number=int(doc.metadata["page_number"]),
                chunk_id=int(doc.metadata["chunk_id"]) if doc.metadata.get("chunk_id") is not None else None,
                chunk_text=doc.page_content,
                score=float(score),
            )
            for doc, score in results
        ]

    prompt = f"""
You are a financial document analysis assistant for fintech workflows.
Answer the user's question using only the provided context.
If the context does not contain enough information, say that the uploaded documents do not provide enough evidence.
Be precise with figures, dates, entities, risk language, and compliance obligations.
Do not invent facts, sources, page numbers, or document names.

Context:
{_format_context(citations)}

Question:
{question}
""".strip()

    if _llm_enabled():
        try:
            response = _chat_model().invoke(prompt)
            answer = str(response.content).strip()
        except Exception as exc:
            logger.exception("Ollama answer generation failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ollama answer generation failed: {str(exc)}",
            ) from exc
    else:
        answer = _local_answer(question, citations)

    history = ChatHistory(
        user_id=user.id,
        question=question,
        answer=answer,
        citations=[citation.model_dump() for citation in citations],
    )
    db.add(history)
    db.commit()

    return ChatResponse(answer=answer, citations=citations)


def get_chat_history(db: Session, user: User) -> list[ChatHistory]:
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user.id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(100)
        .all()
    )
