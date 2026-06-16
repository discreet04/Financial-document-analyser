# Financial Document RAG System

A full-stack Retrieval-Augmented Generation system for fintech document analysis. Users can upload financial PDFs, ask natural-language questions across their document library, receive grounded AI answers with page-level citations, review chat history, and generate executive summaries.

## Stack

- Frontend: React, Vite, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL
- Authentication: JWT bearer tokens
- Vector Search: FAISS
- LLM: OpenAI GPT
- Embeddings: OpenAI `text-embedding-3-small`
- PDF Processing: `pdfplumber`
- RAG Framework: LangChain
- Runtime: Docker and Docker Compose

## Core Capabilities

- User registration and login with password hashing and JWT authentication
- Protected APIs for documents, chat, summaries, and dashboard data
- PDF upload with local storage in an `uploads/` directory
- Page-preserving text extraction from financial PDFs
- Chunking with LangChain `RecursiveCharacterTextSplitter`
- Embedding generation with OpenAI `text-embedding-3-small`
- Per-user FAISS vector indexes with document and page metadata
- Multi-document retrieval across all uploaded user documents
- GPT-generated answers constrained to retrieved context
- Structured citations containing document name, page number, and source chunk text
- ChatGPT-style frontend with citation display
- Persistent chat history in PostgreSQL
- Executive summary generation with key risks, financial highlights, compliance concerns, important findings, and summary text
- Dashboard metrics for documents, chats, and recent activity

## Project Structure

```text
financial-document-rag/
  backend/
    app/
      api/
        routes/
          auth.py
          documents.py
          chat.py
          summaries.py
          dashboard.py
        deps.py
      core/
        config.py
        logging.py
        security.py
      db/
        base.py
        session.py
      models/
        user.py
        document.py
        document_chunk.py
        chat_history.py
      schemas/
        auth.py
        document.py
        chat.py
        summary.py
        dashboard.py
      services/
        auth_service.py
        document_service.py
        pdf_service.py
        vector_store.py
        rag_service.py
        summary_service.py
        dashboard_service.py
      main.py
    uploads/
    vectorstores/
    Dockerfile
    requirements.txt
    alembic.ini
  frontend/
    src/
      api/
      components/
      context/
      pages/
      types/
      App.jsx
      main.jsx
      index.css
    Dockerfile
    package.json
    vite.config.js
    tailwind.config.js
    postcss.config.js
  docker-compose.yml
  .env.example
  README.md
```

## API Design

### Authentication

- `POST /auth/register`
- `POST /auth/login`

### Documents

- `POST /documents/upload`
- `GET /documents`
- `DELETE /documents/{id}`
- `POST /documents/{id}/summary`

### Chat

- `POST /chat/query`
- `GET /chat/history`

### Dashboard

- `GET /dashboard`

## Environment Variables

The project uses environment variables for secrets, database access, OpenAI configuration, CORS, and local storage paths.

```env
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_DB=financial_rag
DATABASE_URL=postgresql+psycopg://rag_user:rag_password@postgres:5432/financial_rag

JWT_SECRET_KEY=replace-with-a-secure-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

OPENAI_API_KEY=replace-with-your-openai-api-key
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

UPLOAD_DIR=uploads
VECTOR_STORE_DIR=vectorstores
BACKEND_CORS_ORIGINS=http://localhost:5173

VITE_API_BASE_URL=http://localhost:8000
```

## Local Development

With Docker, the app will run with:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

For non-Docker local development, set `DATABASE_URL=sqlite:///./financial_rag.db`, start the backend from the `backend/` folder, and start the frontend from the `frontend/` folder. The frontend expects the API at `http://localhost:8000` unless `VITE_API_BASE_URL` is changed.

Uploads and document questions require `OPENAI_API_KEY`. Without it, the API will respond with `OPENAI_API_KEY is not configured` and the frontend will show that message.

## Database Tables

### users

- `id`
- `name`
- `email`
- `password_hash`
- `created_at`

### documents

- `id`
- `user_id`
- `filename`
- `storage_path`
- `upload_date`

### document_chunks

- `id`
- `document_id`
- `user_id`
- `page_number`
- `chunk_index`
- `chunk_text`
- `created_at`

### chat_history

- `id`
- `user_id`
- `question`
- `answer`
- `citations`
- `timestamp`

## RAG Flow

1. A user uploads a PDF.
2. The backend stores the original file under `backend/uploads/`.
3. `pdfplumber` extracts text page by page.
4. LangChain splits page text into overlapping chunks.
5. Chunks are saved in PostgreSQL with document and page metadata.
6. OpenAI generates embeddings for each chunk.
7. FAISS stores vectors and metadata locally under `backend/vectorstores/`.
8. A user asks a question.
9. The backend retrieves top-k relevant chunks across the user's documents.
10. GPT receives only the retrieved context and must answer from that context.
11. The API returns the answer plus structured citations.
12. The chat is persisted in PostgreSQL.

## Migrations

The backend includes Alembic migration scaffolding and an initial schema migration. For local convenience, the FastAPI app also creates missing tables at startup. In production, prefer running migrations explicitly:

```bash
cd backend
alembic upgrade head
```

## Implementation Sequence

This repository is being generated incrementally, one file at a time:

1. `README.md`
2. `.env.example`
3. `docker-compose.yml`
4. Backend dependency and Docker files
5. Backend configuration, database, models, schemas, services, and routes
6. Frontend dependency and build files
7. Frontend API client, auth context, pages, components, and styling
8. Final smoke-test and setup verification
