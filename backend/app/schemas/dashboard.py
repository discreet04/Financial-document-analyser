from datetime import datetime

from pydantic import BaseModel

from app.schemas.document import DocumentRead


class RecentActivity(BaseModel):
    type: str
    label: str
    timestamp: datetime


class DashboardRead(BaseModel):
    total_documents: int
    total_chats: int
    documents: list[DocumentRead]
    recent_activity: list[RecentActivity]
