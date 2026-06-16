from dataclasses import dataclass

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


@dataclass(frozen=True)
class PageChunk:
    page_number: int
    chunk_index: int
    text: str


def extract_pdf_chunks(file_path: str) -> list[PageChunk]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[PageChunk] = []

    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = " ".join(text.split())
            if not text:
                continue

            for chunk_text in splitter.split_text(text):
                chunks.append(
                    PageChunk(
                        page_number=page_index,
                        chunk_index=len(chunks),
                        text=chunk_text,
                    )
                )

    return chunks
