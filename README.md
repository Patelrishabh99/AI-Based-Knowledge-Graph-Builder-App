# 🧠 AI-Based Graph Builder for Enterprise Intelligence

A production-ready, enterprise-grade AI system that combines Knowledge Graphs (Neo4j), Retrieval-Augmented Generation (RAG), and Multi-LLM support into a full-stack web application.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-blue)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Streamlit Frontend                   │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐ │
│  │  Query   │ │ 3D Graph │ │  LLM    │ │ Dashboard │ │
│  │  Panel   │ │  Viewer  │ │ Compare │ │   Panel   │ │
│  └────┬─────┘ └────┬─────┘ └────┬────┘ └─────┬─────┘ │
│       └──────────┬──┴───────────┘─────────────┘       │
└──────────────────┼───────────────────────────────────┘
                   │ REST API
┌──────────────────┼───────────────────────────────────┐
│               FastAPI Backend                         │
│  ┌───────────┐ ┌──────┐ ┌─────┐ ┌────────┐          │
│  │ Query     │ │Cypher│ │ RAG │ │Multi   │          │
│  │ Intel     │ │ Gen  │ │Pipe │ │LLM Svc │          │
│  └───────────┘ └──────┘ └─────┘ └────────┘          │
└──────────────────┼───────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
┌────┴────┐  ┌────┴────┐  ┌────┴────┐
│  Neo4j  │  │Pinecone │  │  Groq   │
│  Graph  │  │ Vectors │  │  LLMs   │
└─────────┘  └─────────┘  └─────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd GraphBuilder
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# .env file is pre-configured
# Edit .env if needed
```

### 3. Load Data into Neo4j
```bash
python -m scripts.load_data
```

### 4. Start Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Start Frontend (new terminal)
```bash
streamlit run frontend/app.py
```

### 6. Open Browser
Navigate to **http://localhost:8501**

## 🐳 Docker Setup
```bash
docker-compose up --build
```

## 📁 Project Structure

```
GraphBuilder/
├── backend/                 # FastAPI backend
│   ├── main.py              # API endpoints
│   ├── config.py            # Settings
│   ├── middleware.py         # Auth & rate limiting
│   ├── models/schemas.py    # Pydantic models
│   └── services/            # Business logic
│       ├── neo4j_service.py      # Graph DB operations
│       ├── llm_service.py        # Multi-LLM manager
│       ├── rag_service.py        # RAG pipeline
│       ├── cypher_generator.py   # NL → Cypher
│       ├── query_intelligence.py # Intent detection
│       ├── session_service.py    # Session memory
│       └── metrics_service.py    # Performance tracking
├── frontend/                # Streamlit UI
│   ├── app.py               # Main application
│   ├── styles.py            # Dark theme CSS
│   └── components/          # UI panels
├── tests/                   # Pytest suite
├── scripts/                 # Data loading
├── .github/workflows/       # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Natural Language Queries** | Ask questions in plain English |
| **Cypher Generation** | Auto-generates Neo4j Cypher queries |
| **RAG Pipeline** | Semantic + Keyword hybrid search |
| **3D Graph Visualization** | Interactive Plotly 3D rendering |
| **Multi-LLM Comparison** | Compare models side-by-side |
| **Enterprise Dashboard** | KPIs, charts, and metrics |
| **Session Memory** | Context-aware follow-up queries |
| **Dark Mode UI** | Premium enterprise design |

## 🛠️ Tech Stack

- **Frontend**: Streamlit, Plotly, Custom CSS
- **Backend**: FastAPI, Python 3.11
- **AI/ML**: LangChain, Groq, HuggingFace
- **Database**: Neo4j, Pinecone
- **DevOps**: Docker, GitHub Actions
