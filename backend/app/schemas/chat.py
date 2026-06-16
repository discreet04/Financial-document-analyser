from datetime import datetime

from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_id: int | None = None


class Citation(BaseModel):
    document_id: int
    document_name: str
    page_number: int
    chunk_id: int | None = None
    chunk_text: str
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class ChatHistoryRead(BaseModel):
    id: int
    question: str
    answer: str
    citations: list[Citation]
    timestamp: datetime

    model_config = {"from_attributes": True}
