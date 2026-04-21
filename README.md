# EduRoad API

> REST API for vocational orientation in the Colombian higher education system. Helps students discover careers aligned with their profile, budget, and regional job market demand.

**Production:** [`eduroad-api.vercel.app`](https://eduroad-api.vercel.app) · **Docs:** [`/api/docs`](https://eduroad-api.vercel.app/api/docs)

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Security](#security)

---

## Overview

EduRoad serves a curated database of Colombian university and technical careers enriched with:

- Real salary data from OLE (Observatorio Laboral de la Educación) 2023
- Employment rates at 12 months post-graduation
- Regional job demand by department
- Accreditation status from SNIES (Sistema Nacional de Información de la Educación Superior)
- A scoring engine that ranks careers by a student's city, socioeconomic stratum, budget, and interests

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Runtime | Python 3.12 |
| ODM | Beanie 1.26 (async MongoDB) |
| Database | MongoDB Atlas |
| Validation | Pydantic v2 |
| Serverless adapter | Mangum |
| Deployment | Vercel (Fluid Compute) |
| Rate limiting | SlowAPI |
| Logging | structlog (JSON in production) |

---

## Architecture

```
client
  └── Vercel (serverless function)
        └── server/api/index.py  ← Mangum ASGI adapter
              └── FastAPI app (main.py)
                    ├── Middleware stack
                    │     ├── SecurityHeaders
                    │     ├── RequestLogging
                    │     ├── CORS
                    │     └── SessionToken auth
                    ├── /api/carreras   ← Router → Service → Repository
                    ├── /api/perfiles   ← Router → Service → Repository
                    └── /api/admin      ← ETL ingestion endpoint
                          └── MongoDB Atlas (eduroad)
```

**Request flow per domain:** `Router` validates the HTTP contract → `Service` applies business logic → `Repository` handles all database access. No domain leaks across layers.

---

## API Reference

Base URL: `https://eduroad-api.vercel.app`

### Careers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/carreras` | Paginated career list. Filters: `categoria`, `tipo`, `page`, `limit` |
| `GET` | `/api/carreras/{slug}` | Career detail by slug |
| `GET` | `/api/carreras/{slug}/stats` | Visit count and engagement stats |
| `POST` | `/api/carreras/recomendaciones` | Personalized career ranking |

**`POST /api/carreras/recomendaciones` — request body:**

```json
{
  "ciudad": "Bogotá",
  "estrato": 3,
  "presupuesto": 5000000,
  "intereses": ["tecnología", "datos"],
  "tipoCarrera": "universitaria",
  "limite": 10
}
```

### Profiles

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/perfiles` | — | Create anonymous profile |
| `GET` | `/api/perfiles/{id}` | Session token | Get profile |
| `PATCH` | `/api/perfiles/{id}` | Session token | Update profile |

Session token is passed via `X-Session-Token` header.

### Admin

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/admin/etl/run` | `X-Admin-Key` | Run ETL ingestion from SNIES or OLE |
| `GET` | `/api/health` | — | Health check + DB status |

### Response codes

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `400` | Validation error / SSRF blocked |
| `401` | Missing or invalid session token |
| `404` | Resource not found |
| `422` | Integrity check error |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

---

## Getting Started

### Prerequisites

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/) package manager
- MongoDB Atlas cluster (free M0 tier works)

### Local setup

```bash
# 1. Clone the repo
git clone https://github.com/Miguel-Bayter/EduRoad-api.git
cd EduRoad-api/server

# 2. Create virtual environment with Python 3.12
uv python install 3.12
uv venv .venv --python 3.12

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your values (see Environment Variables below)

# 5. Run the development server
.venv/Scripts/python.exe -m uvicorn main:app --port 8000 --reload
# Linux/Mac: .venv/bin/python -m uvicorn main:app --port 8000 --reload
```

API will be available at `http://localhost:8000` · Docs at `http://localhost:8000/api/docs`

---

## Environment Variables

Create `server/.env` with the following variables:

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | Yes | MongoDB Atlas connection string — must include database name (`/eduroad`) |
| `CLIENT_ORIGIN` | Yes | Allowed CORS origin (e.g. `http://localhost:3000`) |
| `SESSION_TOKEN_SECRET` | Yes | Secret for session token signing (min 32 chars) |
| `ADMIN_API_KEY_HASH` | Yes | SHA-256 hash of the admin API key |
| `PORT` | No | Server port. Default: `8000` |
| `LOG_LEVEL` | No | `debug` \| `info` \| `warning`. Default: `info` |
| `FORCE_HTTPS` | No | Redirect HTTP to HTTPS. Default: `false` |

**Generate secrets:**

```bash
python3 -c "import secrets, hashlib; k=secrets.token_hex(24); print('ADMIN_API_KEY:', k); print('ADMIN_API_KEY_HASH:', hashlib.sha256(k.encode()).hexdigest())"
python3 -c "import secrets; print('SESSION_TOKEN_SECRET:', secrets.token_hex(32))"
```

---

## Project Structure

```
server/
├── main.py                  # App factory, middleware registration, route mounting
├── config.py                # Pydantic settings (reads .env)
├── requirements.txt         # Pinned production dependencies
├── pyproject.toml           # Project metadata, pytest and ruff config
│
├── app/
│   ├── api/
│   │   ├── carreras/        # Career domain (router, service, repository, schemas)
│   │   ├── perfiles/        # Profile domain (router, service, repository, schemas)
│   │   └── admin/           # Admin endpoints (ETL trigger)
│   │
│   ├── models/              # Beanie documents (MongoDB collections)
│   │   ├── carrera.py
│   │   ├── perfil.py
│   │   ├── audit_log.py
│   │   └── data_fuente_auditoria.py
│   │
│   ├── middleware/
│   │   ├── auth.py          # Session token validation
│   │   ├── logging_mw.py    # Structured request logging
│   │   └── security_headers.py
│   │
│   ├── core/
│   │   └── exceptions.py    # Domain exceptions
│   │
│   ├── db/
│   │   └── mongodb.py       # Motor client, Beanie init, lazy init for serverless
│   │
│   └── utils/
│       ├── etl/             # SNIES CSV and OLE Excel parsers
│       └── logger.py        # structlog configuration
│
├── api/
│   └── index.py             # Mangum handler (Vercel serverless entrypoint)
│
├── scripts/
│   ├── etl_run.py           # CLI ETL runner
│   └── seed_db.py           # Database seeder
│
└── tests/
```

---

## Deployment

The API is deployed as a serverless function on Vercel via the Mangum ASGI adapter. Database initialization is lazy (fires on first request) to avoid cold-start failures from Vercel's disabled lifespan events.

```bash
# Deploy to production
vercel deploy --prod

# View logs
vercel logs https://eduroad-api.vercel.app

# Manage environment variables
vercel env ls
vercel env add VARIABLE_NAME production
```

**Re-deploy after env var changes** — Vercel requires a new deployment for env vars to take effect.

---

## Security

| Mechanism | Implementation |
|---|---|
| CORS | Single allowed origin via `CLIENT_ORIGIN` |
| Session tokens | HMAC-signed, stored server-side in MongoDB |
| Admin key | SHA-256 hashed key checked on every admin request |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` via custom middleware |
| Rate limiting | 30 requests / 15 min on recommendation endpoint (SlowAPI) |
| SSRF protection | Allowlist validation on ETL URLs before HTTP fetch |
| Input validation | Pydantic v2 strict mode on all request bodies |

---

## License

MIT
