# 🐳 AJAX AI - Docker Deployment Guide

This guide explains how to build, run, and deploy AJAX AI using **Docker** and **Docker Compose**.

---

## 🚀 Quick Start with Docker Compose (Recommended)

Docker Compose automatically sets up **AJAX AI** along with a production-ready **PostgreSQL 16** database container and persistent volumes.

### 1. Start Services
```bash
docker compose up -d --build
```

### 2. View Live Logs
```bash
docker compose logs -f ajax-ai
```

### 3. Open AJAX AI in Browser
- **Web Dashboard**: [http://localhost:8000/AJAX](http://localhost:8000/AJAX)
- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Stop Services
```bash
docker compose down
```

---

## 📦 Single Container Build & Run (Standalone)

If you want to run only the AJAX AI container (using high-speed SQLite):

### 1. Build the Docker Image
```bash
docker build -t ajax-ai:latest .
```

### 2. Run the Container
```bash
docker run -d \
  --name ajax-ai-container \
  -p 8000:8000 \
  -v ajax_data:/app/data \
  -e OPENAI_API_KEY="your-key-here" \
  ajax-ai:latest
```

---

## ⚙️ Environment Variables

You can pass environment variables in `.env` or via Docker Compose:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port for the FastAPI web server |
| `DEFAULT_LLM_PROVIDER` | `openai` | Active provider (`openai`, `groq`, `deepseek`, `ollama`) |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `GROQ_API_KEY` | - | Groq Cloud API key |
| `DEEPSEEK_API_KEY` | - | DeepSeek API key |
| `DB_TYPE` | `postgres` | Database type (`postgres` or `sqlite`) |
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `ajax_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `ajax_secure_password` | PostgreSQL password |
| `POSTGRES_DB` | `ajax_db` | PostgreSQL database name |

---

## 🛡️ Healthcheck & Monitoring

The container includes built-in health inspection:
```bash
docker inspect --format='{{json .State.Health}}' ajax-ai-app
```
