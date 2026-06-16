from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardRead
from app.services.dashboard_service import get_dashboard


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardRead)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardRead:
    return get_dashboard(db, current_user)
