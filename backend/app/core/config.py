from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Financial Document RAG"
    api_prefix: str = ""
    environment: str = "development"

    database_url: str = Field(default="sqlite:///./financial_rag.db")

    jwt_secret_key: str = Field(default="replace-with-a-long-random-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_keep_alive: str = "30m"
    ollama_num_ctx: int = 4096
    ollama_chat_num_predict: int = 450
    ollama_summary_num_predict: int = 650
    embedding_provider: str = "huggingface"
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    rag_top_k: int = 3
    chunk_size: int = 1200
    chunk_overlap: int = 200
    summary_context_chars: int = 8000
    summary_citation_limit: int = 6

    upload_dir: str = "uploads"
    vector_store_dir: str = "vectorstores"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
