from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.document import Document
from app.models.user import User
from app.schemas.dashboard import DashboardRead, RecentActivity


def get_dashboard(db: Session, user: User) -> DashboardRead:
    total_documents = db.scalar(select(func.count(Document.id)).where(Document.user_id == user.id)) or 0
    total_chats = db.scalar(select(func.count(ChatHistory.id)).where(ChatHistory.user_id == user.id)) or 0

    documents = list(db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.upload_date.desc()).limit(10)))
    chats = list(db.scalars(select(ChatHistory).where(ChatHistory.user_id == user.id).order_by(ChatHistory.timestamp.desc()).limit(10)))

    recent_activity = [
        RecentActivity(type="document", label=f"Uploaded {document.filename}", timestamp=document.upload_date)
        for document in documents[:5]
    ]
    recent_activity.extend(
        RecentActivity(type="chat", label=chat.question[:100], timestamp=chat.timestamp)
        for chat in chats[:5]
    )
    recent_activity.sort(key=lambda item: item.timestamp, reverse=True)

    return DashboardRead(
        total_documents=total_documents,
        total_chats=total_chats,
        documents=documents,
        recent_activity=recent_activity[:10],
    )
