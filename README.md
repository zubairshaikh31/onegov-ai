# 🇮🇳 OneGov AI — Refactored & Production-Ready

**One Platform. Every Government Service.**

AI-powered platform for Indian citizens to discover, understand, and access government services.

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/your-username/onegov-ai.git
cd onegov-ai

# 2. Setup (copies .env files, starts Docker, migrates DB, seeds data)
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Or manually:**

```bash
cp .env.example .env
# backend/.env is already included for development

docker compose up -d

# Wait for services, then migrate
docker compose exec backend alembic upgrade head

# Seed sample data
docker compose exec backend python scripts/seed.py

# Pull Ollama model (~2GB)
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text

# Install frontend dependencies (if running locally outside Docker)
cd frontend && npm install && cd ..
```

---

## URLs

| Service       | URL                        |
|---------------|----------------------------|
| Frontend      | http://localhost:3000       |
| Backend API   | http://localhost:8000       |
| Swagger Docs  | http://localhost:8000/docs  |
| Nginx Proxy   | http://localhost:80         |

**Default credentials:**

| Role  | Email             | Password      |
|-------|-------------------|---------------|
| Admin | admin@onegov.ai   | Admin@1234!   |
| User  | user@onegov.ai    | User@1234!    |

---

## Architecture

```
frontend/          Next.js 15 + React 19 + TypeScript
backend/           FastAPI + SQLAlchemy 2.0 + PostgreSQL
ai/                LLM provider abstraction (Ollama/OpenAI/Gemini/Groq)
docker/            Nginx reverse proxy config
scripts/           Setup and seed scripts
migrations/        Alembic database migrations
```

## AI Provider

Default: **Ollama (llama3.2)** — free, local, no API key needed.

Switch providers by changing `LLM_PROVIDER` in `backend/.env`:

```env
LLM_PROVIDER=openai    # requires OPENAI_API_KEY
LLM_PROVIDER=gemini    # requires GEMINI_API_KEY
LLM_PROVIDER=groq      # requires GROQ_API_KEY
LLM_PROVIDER=ollama    # default, free
```

## Useful Commands

```bash
make up              # Start all services
make migrate         # Run Alembic migrations
make seed            # Seed database
make test            # Run backend tests
make pull-models     # Pull Ollama AI models
make logs svc=backend  # Watch service logs
```

---

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ | Blueprint & architecture |
| 1 | ✅ | Foundation, auth, database, Docker |
| 2 | ✅ | Services, Schemes, Search APIs |
| 3 | 🔜 | Semantic search with pgvector + RAG |
| 4 | 📅 | Advanced AI: eligibility, OCR, voice |
| 5 | 📅 | Admin dashboard & analytics |
| 6 | 📅 | PWA, multilingual, notifications |

---

*Built for Digital India 🇮🇳*
