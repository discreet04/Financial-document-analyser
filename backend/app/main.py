import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.api.routes import auth, chat, dashboard, documents, summaries
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter


configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
def warm_local_models() -> None:
    if settings.embedding_provider.strip().lower() == "huggingface":
        try:
            from app.services.vector_store import _embedding_model

            _embedding_model().embed_query("warm up embedding model")
            logger.info("Hugging Face embedding model warmed")
        except Exception:
            logger.exception("Hugging Face embedding warm-up failed")

    if settings.llm_provider.strip().lower() == "ollama":
        try:
            from app.services.rag_service import _chat_model

            _chat_model().invoke("Reply with OK.")
            logger.info("Ollama chat model warmed")
        except Exception:
            logger.exception("Ollama chat warm-up failed")


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(summaries.router)
app.include_router(dashboard.router)
