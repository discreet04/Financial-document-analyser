from pydantic import BaseModel

from app.schemas.chat import Citation


class ExecutiveSummary(BaseModel):
    executive_summary: str
    key_risks: list[str]
    financial_highlights: list[str]
    compliance_concerns: list[str]
    important_findings: list[str]
    citations: list[Citation]
