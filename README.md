# Job Ready Platform

A modern job-preparation platform covering aptitude, DSA, coding, SQL, AI/ML, interviews, assessments, and job tracking.

**Build 1** delivers the foundation: application shell, routing, API scaffolding, PostgreSQL/Redis connectivity, and Docker Compose infrastructure.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React, Vite, TypeScript, Tailwind CSS, React Router, TanStack Query, Axios, Lucide |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Data | PostgreSQL, Redis |
| Infra | Docker, Docker Compose |

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose

## Quick Start (Local Development)

### 1. Clone and configure environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### 2. Start PostgreSQL and Redis

```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend setup (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### 5. Verify

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Modules: http://localhost:8000/api/v1/modules

## Full Stack via Docker Compose

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

## Project Structure

```
job-ready-platform/
├── frontend/          # React + Vite application
├── backend/           # FastAPI application
├── infra/             # Docker configuration
├── docs/              # Architecture and development docs
├── .env.example
└── README.md
```

## API Endpoints (Build 1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service health check |
| GET | `/api/v1/modules` | Enabled platform modules |

## Running Tests

```bash
cd backend
pytest
```

```bash
cd frontend
npm run build
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Product Modules](docs/PRODUCT_MODULES.md)
- [Donor Repositories](docs/DONOR_REPOS.md)
- [Development Guide](docs/DEVELOPMENT.md)

## License

Proprietary — Job Ready Platform
