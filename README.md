# Financial Document Analyser

A full-stack AI-powered Financial Document Analysis platform built using Retrieval-Augmented Generation (RAG). Users can upload financial reports, annual statements, corporate filings, and other PDF documents, then interact with them using natural language to obtain source-grounded answers, executive summaries, and document insights.

The system combines semantic search, vector embeddings, and Large Language Models to provide accurate responses with page-level citations.

---

## Features

### Authentication & User Management

* User registration and login
* JWT-based authentication
* Protected API routes
* User-specific document libraries

### Document Processing

* PDF upload and storage
* Page-level text extraction
* Intelligent text chunking
* Metadata generation
* Document management (upload, delete, list)

### Retrieval-Augmented Generation (RAG)

* Semantic search using FAISS
* Hugging Face embeddings
* Ollama (Llama 3) integration
* Context-aware question answering
* Source-grounded responses
* Page-level citations
* Document-specific retrieval filtering

### Executive Summaries

* AI-generated executive summaries
* Key risks identification
* Financial highlights extraction
* Compliance concerns detection
* Important findings generation

### Dashboard & Analytics

* Document statistics
* Chat history
* Recent activity tracking
* Source management interface

---

## Technology Stack

### Frontend

* React
* Vite
* Tailwind CSS
* Axios

### Backend

* FastAPI
* SQLAlchemy
* Pydantic
* Alembic

### Database

* PostgreSQL

### AI & RAG

* LangChain
* Hugging Face Embeddings (`all-MiniLM-L6-v2`)
* Ollama
* Llama 3
* FAISS Vector Store

### PDF Processing

* PyPDF / PDF Extraction Services

### Infrastructure

* Docker
* Docker Compose

---

## Architecture Overview

User Upload PDF
↓
React Frontend
↓
FastAPI Backend
↓
PDF Extraction
↓
Text Chunking
↓
Metadata Creation
↓
PostgreSQL Storage
↓
Hugging Face Embeddings
↓
FAISS Vector Store
↓
Document-Specific Retrieval
↓
Ollama (Llama 3)
↓
Source-Grounded Answer + Citations

---

## Core Capabilities

* Upload and analyze financial documents
* Ask questions about uploaded PDFs
* Generate document summaries
* Retrieve information with source citations
* Perform semantic search across document content
* Prevent cross-document retrieval contamination using document-specific filtering
* Maintain persistent chat history
* Store metadata and document chunks in PostgreSQL
* Generate context-aware answers using local LLMs

---

## Project Structure

```text
financial-document-analyser/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── uploads/
│   ├── vectorstores/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── context/
│   │   └── App.jsx
│   │
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

---

## API Endpoints

### Authentication

```http
POST /auth/register
POST /auth/login
```

### Documents

```http
POST /documents/upload
GET /documents
DELETE /documents/{id}
POST /documents/{id}/summary
```

### Chat

```http
POST /chat/query
GET /chat/history
```

### Dashboard

```http
GET /dashboard
```

---

## Environment Variables

```env
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_DB=financial_rag

DATABASE_URL=postgresql+psycopg://rag_user:rag_password@postgres:5432/financial_rag

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

UPLOAD_DIR=uploads
VECTOR_STORE_DIR=vectorstores

BACKEND_CORS_ORIGINS=http://localhost:5173

OLLAMA_MODEL=llama3
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

VITE_API_BASE_URL=http://localhost:8000
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/financial-document-analyser.git

cd financial-document-analyser
```

### Start Ollama

```bash
ollama pull llama3
ollama serve
```

### Run Application

```bash
docker compose up --build
```

---

## Access Application

Frontend

```text
http://localhost:5173
```

Backend

```text
http://localhost:8000
```

Swagger API Docs

```text
http://localhost:8000/docs
```

---

## RAG Workflow

### Document Ingestion

1. User uploads a PDF.
2. Backend extracts text from each page.
3. Text is split into chunks.
4. Metadata is attached:

   * document_id
   * document_name
   * page_number
   * chunk_id
5. Chunks are stored in PostgreSQL.

### Indexing

1. Hugging Face generates embeddings.
2. Embeddings are stored in FAISS.
3. User-specific vector indexes are maintained.

### Question Answering

1. User selects a document.
2. Query is sent to backend.
3. Retrieval is filtered using document_id.
4. Top relevant chunks are fetched.
5. Context and citations are sent to Llama 3.
6. LLM generates an answer.
7. Source citations are returned.

---

## Future Improvements

* Multi-document comparison mode
* Financial ratio analysis
* OCR support for scanned PDFs
* Export chat conversations
* Advanced analytics dashboard
* Cloud deployment (AWS/Azure/GCP)
* Role-based access control

---

## Author

Developed as a full-stack Generative AI project demonstrating:

* Retrieval-Augmented Generation (RAG)
* Vector Databases
* LangChain
* FastAPI
* React
* PostgreSQL
* Hugging Face
* Ollama
* Docker

