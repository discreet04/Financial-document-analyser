from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.summary import ExecutiveSummary
from app.services.summary_service import generate_summary


router = APIRouter(prefix="/documents", tags=["Summaries"])


@router.post("/{document_id}/summary", response_model=ExecutiveSummary)
def summary(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutiveSummary:
    return generate_summary(db, current_user, document_id)
