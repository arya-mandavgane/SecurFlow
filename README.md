# SecurFlow – Security Deposit & FDR Management Portal for AICTE

> **Tagline:** One Platform. Complete FDR Lifecycle. Smarter Compliance.

SecurFlow is an AI-powered enterprise portal designed for the All India Council for Technical Education (AICTE) to centralize, verify, track, and manage Fixed Deposit Receipts (FDRs) and Security Deposits submitted by technical institutions nationwide.

---

## Architecture Overview

```
securflow/
├── frontend/            # React 18 + TypeScript + Vite + Tailwind CSS + Material UI
├── backend/             # Django 5 + Django REST Framework + Celery
├── ai-service/          # FastAPI + PyMuPDF + pgvector RAG Assistant
├── ocr-service/         # FastAPI + PaddleOCR + PyMuPDF Extraction Service
├── docker-compose.yml   # Multi-service orchestration
├── .env.example         # Template configuration
└── README.md
```

### Services & Ports (Default)

| Service | Port | Description |
|---|---|---|
| `frontend` | `3000` | Institution & Official Web Portal |
| `backend` | `8000` | Core Django REST Framework API |
| `ai-service` | `8001` | RAG Knowledge Assistant & Query Service |
| `ocr-service` | `8002` | PaddleOCR & PDF Extraction Microservice |
| `postgres` | `5432` | PostgreSQL 16 with `pgvector` enabled |
| `redis` | `6379` | Cache and Celery message broker |
| `celery-worker` | - | Background task processing (OCR, alerts, reports) |
| `celery-beat` | - | Scheduled maturity tracker & recurring notifications |

---

## Quickstart with Docker Compose

1. **Clone the repository and copy environment variables:**
   ```bash
   cp .env.example .env
   ```

2. **Start all services:**
   ```bash
   docker compose up --build -d
   ```

3. **Run database migrations and seed realistic demo data:**
   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py seed_demo_data
   ```

4. **Verify Health Endpoints:**
   - Backend API: `http://localhost:8000/api/health/`
   - AI Service: `http://localhost:8001/health`
   - OCR Service: `http://localhost:8002/health`
   - Frontend UI: `http://localhost:3000`

---

## Seed Accounts (After running `seed_demo_data`)

| Role | Username / Email | Password | Purpose |
|---|---|---|---|
| **Admin** | `admin@aicte.gov.in` | `SecurFlow@2026` | Full platform administration |
| **Official** | `official1@aicte.gov.in` | `SecurFlow@2026` | AICTE Document Verification Officer |
| **Official** | `official2@aicte.gov.in` | `SecurFlow@2026` | AICTE Senior Verification Officer |
| **Institution** | `principal@vjti.ac.in` | `SecurFlow@2026` | VJTI Mumbai (1-109724121) |
| **Institution** | `registrar@coep.ac.in` | `SecurFlow@2026` | COEP Tech Pune (1-109823451) |

---

## Local Development (Without Docker)

### Backend (Django)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 8000
```

### AI Service (FastAPI)
```bash
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

### OCR Service (FastAPI)
```bash
cd ocr-service
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
