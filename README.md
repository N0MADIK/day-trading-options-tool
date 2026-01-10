# Options Scanner Pro + Finance Flow

> Advanced Options Scanner with AI-Powered Trade Recommendations, Interactive Charts, Real-Time Greeks, and Personal Finance Dashboard

![Options Scanner](https://img.shields.io/badge/Options-Scanner-00d26a) ![AI Powered](https://img.shields.io/badge/AI-Gemini-4a9eff) ![React](https://img.shields.io/badge/React-18-61dafb) ![Python](https://img.shields.io/badge/Python-FastAPI-3776ab)

---

## 🏗️ Architecture Overview

This project consists of two frontends sharing a single FastAPI backend:

| Component | Description | Port |
|-----------|-------------|------|
| **Backend** | FastAPI with UUID-based auth, personal finance, trading | `8420` |
| **Options Frontend** | Original options scanner UI | `5420` |
| **Frontend v2** | Personal finance dashboard (React + Vite) | `3000` |

### Backend Design

The backend uses a **layered architecture**:

```
backend/
├── app/
│   ├── api/v1/routers/    # API endpoints
│   ├── models/            # SQLAlchemy ORM models (UUID-based)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic
│   ├── repositories/      # Data access layer
│   ├── domain/            # Domain models (legacy)
│   ├── infrastructure/    # Database, external services
│   └── core/              # Config, dependencies, security
├── migrations/            # SQL migrations
└── tests/                 # Pytest test suites
```

### Key API Endpoints

| Endpoint Group | Prefix | Purpose |
|----------------|--------|---------|
| Auth | `/api/v1/auth/*` | Login, register, JWT tokens |
| Profiles | `/api/v1/profiles/*` | User profiles |
| Roles | `/api/v1/roles/*` | RBAC, admin checks |
| Connected Accounts | `/api/v1/connected-accounts/*` | Bank/brokerage links |
| Market Data | `/api/v1/market/*` | Quotes, options chains |
| Net Worth | `/api/v1/net-worth/*` | Financial tracking |
| WebSocket | `/api/v1/ws/connect` | Real-time updates |

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# 1. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 2. Build and start all services
docker-compose up -d --build

# Access:
# - Options Scanner: http://localhost:5420
# - Finance Flow: http://localhost:3000
# - Backend API: http://localhost:8000/docs
```

### Local Development

**Backend:**
```bash
cd backend

# Create virtual environment and install deps
uv venv
uv sync

# Run the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Options Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on :5173 in dev, :5420 in Docker
```

**Frontend v2 (Finance Dashboard):**
```bash
cd frontend_v2
npm install

# Create .env.local for local development
echo "VITE_API_URL=http://localhost:8420/api" > .env.local

npm run dev  # Runs on :5173
```

---

## 📦 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up -d --build

# Stop everything
docker-compose down

# Production (uses pre-built images)
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 Making Backend Updates

When adding new features to the backend:

### 1. Create the Model (`app/models/`)
```python
# Use UUID primary keys
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MyModel(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

### 2. Create the Schema (`app/schemas/`)
```python
from pydantic import BaseModel
from uuid import UUID

class MyModelResponse(BaseModel):
    id: UUID
    # ... fields
    class Config:
        from_attributes = True
```

### 3. Create the Router (`app/api/v1/routers/`)
```python
from app.infrastructure.db import get_async_session  # Use this for session
from app.core.deps import get_current_user           # For auth

router = APIRouter(prefix="/my-endpoint", tags=["my-endpoint"])
```

### 4. Register the Router (`app/api/v1/router.py`)
```python
from app.api.v1.routers import my_router
api_router.include_router(my_router.router)
```

### 5. Add Migration (`migrations/`)
Create a SQL file with table definitions.

### Common Issues

| Issue | Solution |
|-------|----------|
| `ImportError: email-validator` | Run `uv add email-validator` |
| `ImportError: get_async_session` | It's an alias for `get_db` in `infrastructure/db.py` |
| Circular imports | Move imports inside functions, avoid service imports at module level |

---

## 🗄️ Database Migration

Run the SQL migration to create new tables:

```bash
# For PostgreSQL
psql -U postgres -d your_database -f backend/migrations/001_finance_flow_integration.sql

# For SQLite (development)
# Tables are auto-created by SQLAlchemy on first run
```

---

## 🧪 Testing

```bash
cd backend

# Run all tests
uv run python -m pytest tests/ -v

# Run finance-flow integration tests only
uv run python -m pytest tests/test_finance_flow_integration.py -v

# Run with coverage
uv run python -m pytest --cov=app tests/
```

---

## 📁 Environment Variables

**Backend (`backend/.env`):**
```env
# Required
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite+aiosqlite:///./data/trading.db

# Optional - Financial Integrations
PLAID_CLIENT_ID=
PLAID_SECRET=
SNAPTRADE_CLIENT_ID=
SNAPTRADE_CONSUMER_KEY=

# Security
JWT_SECRET_KEY=your-secret-key
FINANCE_ENCRYPTION_KEY=  # For encrypting API keys
```

**Frontend v2 (`frontend_v2/.env.local`):**
```env
# Local development (direct backend)
VITE_API_URL=http://localhost:8420/api

# Docker (leave empty - uses nginx proxy)
# VITE_API_URL=
```

---

## 🤖 AI Features

- **AI Trade Advisor**: Gemini 2.5 Flash analysis across 5 timeframes
- **Smart Strike Selection**: Targets ATM/Near-OTM options (Delta 0.15-0.85)
- Customize prompts in `backend/services/options.py`

---

## 📋 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Frontend | React 18, Vite, TailwindCSS |
| Database | PostgreSQL (prod), SQLite (dev) |
| AI | Google Gemini 2.5 Flash |
| Auth | JWT tokens, UUID-based users |
| Real-time | WebSockets |

---

## ⚠️ Disclaimer

For educational purposes only. Options trading involves significant risk. Always do your own research.

## License

MIT

