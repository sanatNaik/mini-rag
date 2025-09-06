# Mini RAG Application

A minimal RAG (Retrieval-Augmented Generation) project built with:
- Flask backend (for embeddings, retrieval, and OpenAI/OpenRouter integration)
- React (Vite) frontend (for user interaction)
- Pinecone vector database for storage & retrieval
- Jina Reranker for reranking retrieved data
- OpenAI api for embedding text data
- Open Router for accessing LLM model
- Render for backend deployment
- Vercel for frontend deployment

---

## 🚀 Features
- Upload text for embeddings
- Store & retrieve context using Pinecone
- Generate answers using OpenRouter models
- Rerank retrieved context for relevance
- Full-stack deployment with separate backend & frontend

---

## 🗂️ Folder Structure
project/
├── backend/
│ ├── app.py # Flask backend entry point
│ ├── requirements.txt # Backend dependencies
│ ├── .env # Environment variables (NOT in Git)
│ └── ...
├── frontend/
│ ├── src/
│ │ ├── App.jsx # Main React component
│ │ ├── components/ # UI components
│ │ └── ...
│ ├── package.json
│ └── vite.config.js
└── README.md

### ARCHITECTURE
---
                ┌───────────────────────────┐
                │        Frontend (React)    │
                │ Vite + Context + Fetch API │
                └─────────────▲─────────────┘
                              │
                      REST API Calls (JSON)
                              │
        ┌─────────────────────┴──────────────────────┐
        │            Backend (FastAPI)               │
        │  Retriever → Reranker → Answer Generator   │
        └───────────────▲───────────────┬────────────┘
                        │               │
                    LLM Response  Embeddings(OPEN AI)
                        │               │
                   Jina Reranker        |
                        │               │
                Pinecone Vector DB  <───┘





## ⚙️ Backend Setup (Flask)

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt

### Add api keys
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
..
etc

### Run backend locally

python app.py

Frontend Setup (React + Vite)
1. Install dependencies
cd frontend
npm install

2. Run frontend locally
npm run dev


Frontend runs at: http://localhost:5173

☁️ Deployment
Backend (Render)

Push code to GitHub

Create a new Render Web Service

Set:

Root Directory: backend

Start Command: gunicorn app:app

Add environment variables in Render Dashboard

Deploy & get backend URL (e.g., https://mini-rag-1.onrender.com)


### Backend

Framework: FastAPI

Main Components:

Retriever:

Embedding generation using OpenAI text-embedding-3-small

Vector store: Pinecone

Query top-k results → metadata + text chunks

Reranker:

Uses Jina Reranker API (jina-reranker-v2-base-multilingual)

Scores and sorts retrieved chunks by relevance

Answer Generator:

Uses OpenRouter → openai/gpt-oss-20b:free model

Generates answers strictly from reranked context

### Retriever Settings
Parameter	Value
Vector Dimension	1536
Embedding Model	text-embedding-3-small (OpenAI)
Vector DB	Pinecone
Metric	Cosine similarity
Top-k Retrieved	5

### Reranker Settings
Parameter	Value
Model	jina-reranker-v2-base-multilingual
API Provider	Jina AI
Top-N Returned	3

### Chunking Parameters
Parameter	Value
Chunk Size	500
Overlap	50
Metadata Stored	text, source, section_title, position

### Providers Used
Component	Provider/API
Embeddings	OpenAI text-embedding-3-small
Vector Storage	Pinecone
Reranker	Jina AI Reranker
Answer Generator	OpenRouter openai/gpt-oss-20b:free
Backend Hosting	Render
Frontend Hosting	Vercel

License

This project is licensed under the MIT License.



