from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import delete_document, list_documents, upload_document


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentRead, status_code=201)
@limiter.limit("10/minute")
def upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    return upload_document(db, current_user, file)


@router.get("", response_model=list[DocumentRead])
def documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentRead]:
    return list_documents(db, current_user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    delete_document(db, current_user, document_id)
