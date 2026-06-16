from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatHistoryRead, ChatQuery, ChatResponse
from app.services.rag_service import answer_question, get_chat_history


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatResponse)
@limiter.limit("30/minute")
def query(
    request: Request,
    payload: ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    return answer_question(db, current_user, payload.question, payload.top_k, payload.document_id)


@router.get("/history", response_model=list[ChatHistoryRead])
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatHistoryRead]:
    return get_chat_history(db, current_user)
