from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    filename: str
    upload_date: datetime

    model_config = {"from_attributes": True}


class DocumentChunkRead(BaseModel):
    id: int
    document_id: int
    page_number: int
    chunk_index: int
    chunk_text: str

    model_config = {"from_attributes": True}
