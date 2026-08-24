# TrustShare Project Handoff

> Purpose: This file gives a new IDE, developer, or coding assistant the complete context required to continue the project safely. Read this file before making changes.

## 1. Project Overview

**Project name:** TrustShare  
**Goal:** Build a production-oriented secure file-sharing and digital collaboration platform.

The platform will let authenticated users upload, organize, encrypt, and securely share files. Access is governed by roles, file ownership, direct permissions, and temporary share links.

### Required capabilities from the project brief

- User registration, login, JWT authentication, roles, and future MFA/OAuth support
- File upload, folders, metadata, search/filtering, and version management
- Server-side file encryption before storage
- Temporary share links with expiry, permissions, revocation, and download limits
- Download tracking, audit logging, alerts, notifications, and analytics
- Docker-based development and eventual cloud deployment

## 2. Approved Technology Decisions

| Area | Choice | Status |
|---|---|---|
| Frontend | React.js + Vite | Initialized |
| Backend | Python + FastAPI | Initialized |
| Core relational database | PostgreSQL | Running locally in Docker |
| Audit/event logging | MongoDB | Planned; not configured yet |
| Cache/rate limiting | Redis | Planned; not configured yet |
| File storage | Local development storage, then AWS S3/Azure Blob | Planned |
| Encryption | AES-256-GCM, unique data-encryption key per file | Design approved; not implemented |
| ORM/migrations | SQLAlchemy + Alembic | Planned; not installed/configured yet |
| Containers | Docker Compose | PostgreSQL service working |

## 3. Current Repository State

**Repository:** `https://github.com/mitanshu02/TrustShare.git`  
**Branch:** `main`

### Current structure

```text
trustshare/
├── backend/
│   ├── .venv/                     # local Python virtual environment; ignored by Git
│   └── app/
│       └── main.py                # FastAPI health-check application
├── docs/
│   ├── architecture.md
│   ├── databse-design.md           # existing name has a typo; see note below
│   └── security-design.md
├── frontend/                       # React + Vite application
├── .env                            # local secrets; ignored by Git
├── .env.example                    # safe environment-variable template
├── .gitignore
├── compose.yaml                    # PostgreSQL Docker Compose service
├── LICENSE
└── README.md
```

### Important naming note

The existing file is named `docs/databse-design.md` (missing the second `a`). It contains the correct database design. Rename it later for clarity, using Git so history is preserved:

```powershell
git mv docs/databse-design.md docs/database-design.md
```

Do not rename it outside Git.

## 4. What Is Already Working

### Frontend

- React application initialized with Vite in `frontend/`.
- Node.js used: `v20.19.6`.
- npm used: `10.8.2`.

Run it:

```powershell
cd frontend
npm install
npm run dev
```

Vite normally serves the app at `http://localhost:5173`.

### Backend

`backend/app/main.py` currently contains a minimal FastAPI application with a health check:

```python
from fastapi import FastAPI

app = FastAPI(title="TrustShare API")


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "TrustShare backend is running"}
```

Run it from `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Verify:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

The endpoint has already been verified successfully.

### Docker and PostgreSQL

- Docker Desktop is installed and verified with `docker run hello-world`.
- Docker version verified: `29.7.2`.
- Docker Compose version verified: `v5.4.0`.
- WSL 2 is installed and working.
- PostgreSQL container name: `trustshare-postgres`.
- Image: `postgres:16-alpine`.
- Host port: `5432`.
- The container has reached the `healthy` state.

Start PostgreSQL from the repository root:

```powershell
docker compose up -d postgres
docker compose ps
```

Stop PostgreSQL without deleting data:

```powershell
docker compose down
```

Inspect logs:

```powershell
docker compose logs postgres
```

Verify the database connection after the container is healthy:

```powershell
docker compose exec postgres psql -U trustshare_user -d trustshare_db -c "SELECT current_database(), current_user;"
```

## 5. Environment Variables and Secret Rules

The root `.env` file is intentionally ignored by Git. It must never be committed or pasted into tickets, commits, chat, or documentation.

Required local PostgreSQL variables:

```env
POSTGRES_DB=trustshare_db
POSTGRES_USER=trustshare_user
POSTGRES_PASSWORD=<use-a-strong-local-password>
POSTGRES_PORT=5432
```

`.env.example` has the same variable names without a real password and is safe to commit.

Future secrets include `JWT_SECRET_KEY`, encryption master-key/KMS configuration, cloud storage credentials, and email-provider credentials. Keep all of them outside source control.

## 6. Docker Compose Configuration

`compose.yaml` currently runs only PostgreSQL. This is intentional: the project is being built incrementally.

```yaml
name: trustshare

services:
  postgres:
    image: postgres:16-alpine
    container_name: trustshare-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

The named Docker volume `trustshare_postgres_data` retains PostgreSQL data when the container is stopped or recreated. Do **not** run `docker compose down -v` unless intentionally deleting all local database data.

## 7. Architecture and Diagram Information

The architectural documentation lives in `docs/architecture.md`. It contains a Mermaid high-level diagram and these core flow rules:

```text
React frontend
    -> HTTPS + JWT
FastAPI backend
    -> PostgreSQL for users, metadata, permissions, share links
    -> Redis for rate limits and temporary/token controls
    -> MongoDB for audit/security logs
    -> encrypted object storage for file ciphertext
    -> KMS/secrets manager for production keys and credentials
```

Security trust zones:

1. **Public zone:** React browser client and public share-link users.
2. **Perimeter controls:** TLS/HTTPS, CORS, security headers, request-size limits, and rate limiting.
3. **Application trust zone:** FastAPI, validation, authentication, authorization, upload controls, encryption, and audit-event creation.
4. **Protected data/key zone:** PostgreSQL, Redis, audit-log store, encrypted object storage, and a secrets/KMS service.

## 8. Security Decisions That Must Not Be Changed Casually

- Use **AES-256-GCM**, not unauthenticated AES modes.
- Encrypt every file on the server before it reaches cloud/object storage.
- Use a unique encryption key per uploaded file.
- Store only an encryption-key reference in PostgreSQL; never expose raw file keys to users.
- Use bcrypt password hashing; never store plaintext passwords.
- Use JWT access tokens and later add refresh-token handling.
- Enforce authorization in FastAPI on every protected endpoint. Frontend visibility is not permission enforcement.
- Store only a hash of a share-link token, never the raw token.
- Validate upload size, MIME type, extension, and permissions. Add malware scanning integration before production deployment.
- Decrypt approved downloads temporarily in memory; do not write plaintext files to persistent disk.
- Record authentication, upload, permission, sharing, download, and denied-access events.
- Do not hard-code secrets or commit `.env` files.

The complete rationale and requirements are in `docs/security-design.md`.

## 9. Approved PostgreSQL Data Model

The database design is documented in `docs/databse-design.md`. The approved core PostgreSQL tables are:

| Table | Purpose |
|---|---|
| `users` | User identity, password hash, role, account status |
| `folders` | User-owned folders and optional parent-folder hierarchy |
| `files` | File metadata and encrypted-object-storage reference |
| `file_versions` | Historical encrypted versions of files |
| `file_permissions` | Direct per-user `view` or `download` access |
| `share_links` | Temporary secure sharing links, expiry, revoke state, limits |
| `downloads` | Download tracking data |

Database conventions:

- UUID primary keys
- Timestamp fields (`created_at`, `updated_at`) on major entities
- Unique email addresses
- Soft deletion for files through `deleted_at`
- `access_level` values: `view` or `download`
- One direct-permission record per user per file

Detailed audit/security events belong in MongoDB, not this core relational schema.

## 10. Git Status and Required First Commit

At the time this handoff was written, these local changes still needed to be committed:

- Modified: `.gitignore`
- New: `.env.example`
- New: `compose.yaml`
- New: `docs/architecture.md`
- New: `docs/security-design.md`
- New: `PROJECT_HANDOFF.md`

Before switching IDEs, commit and push the safe files:

```powershell
git add .gitignore .env.example compose.yaml docs PROJECT_HANDOFF.md
git commit -m "Add project architecture, security docs, PostgreSQL Docker setup, and handoff"
git push
```

Check that `.env` was not staged:

```powershell
git status
```

## 11. Exact Next Implementation Steps

Do these in order. Do not jump directly to file uploads or encryption yet.

### Step 1 — Verify the local database connection

```powershell
docker compose ps
docker compose exec postgres psql -U trustshare_user -d trustshare_db -c "SELECT current_database(), current_user;"
```

Expected database/user: `trustshare_db` and `trustshare_user`.

### Step 2 — Add backend database dependencies

From `backend/`, activate the virtual environment and install:

```powershell
.\.venv\Scripts\Activate.ps1
pip install sqlalchemy "psycopg[binary]" alembic pydantic-settings
pip freeze > requirements.txt
```

Review `requirements.txt` before committing it.

### Step 3 — Add application configuration

Create a configuration module that reads `DATABASE_URL` from environment variables. Do not hard-code a password.

The local backend connection format will be:

```text
postgresql+psycopg://trustshare_user:<password>@localhost:5432/trustshare_db
```

Add `DATABASE_URL` to `.env.example` using a placeholder password. Keep the real value only in `.env`.

### Step 4 — Configure SQLAlchemy and Alembic

- Create a SQLAlchemy declarative base.
- Create an engine and request-scoped session dependency.
- Initialize Alembic.
- Configure Alembic to use `DATABASE_URL`.
- Verify an empty migration can run against the Docker PostgreSQL instance.

### Step 5 — Implement models and the first migration

Implement the core schema in a deliberate order:

1. `users`
2. `folders`
3. `files`
4. `file_versions`
5. `file_permissions`
6. `share_links`
7. `downloads`

Create and apply Alembic migrations. Never create production schemas manually through pgAdmin.

### Step 6 — Build authentication before file features

- Registration endpoint
- bcrypt password hashing
- Login endpoint
- JWT access token generation/validation
- Role model and protected endpoint test

### Step 7 — Build basic file metadata management

- Create folders
- Save file metadata
- List the current user’s files
- Apply ownership checks

Only after this basic workflow is tested should server-side encryption, object storage, sharing links, audit logging, Redis, and MongoDB be added.

## 12. Milestone Plan

### Milestone 1 — Foundation, authentication, and basic file management

Architecture/design documents, project initialization, frontend/backend foundation, PostgreSQL/Docker configuration, authentication, roles, secure upload validation, and a file dashboard.

**Current position:** Design documentation and initial environment setup are complete. Database connection verification and backend ORM/migration work are next.

### Milestone 2 — Encryption and secure sharing

AES-256-GCM encryption, object storage, in-memory decryption, key handling, share links, expiry, permissions, and restrictions.

### Milestone 3 — Monitoring and analytics

Audit logs, notifications, security alerts, download activity, suspicious-activity detection, and dashboards.

### Milestone 4 — Quality and deployment

Security testing, API/frontend tests, responsive UI, full Docker services, cloud deployment, documentation, and final demonstration.

## 13. Working Style for the Next IDE/Assistant

- Work in small, testable Agile tasks.
- Complete and verify one task before starting the next.
- Keep commits focused and descriptive.
- Never use force pushes, hard resets, or delete Docker volumes without explicit approval.
- Preserve user changes and inspect Git status before changing files.
- Add or update documentation whenever an architectural, data-model, security, or environment decision changes.
- Treat this as a production-quality security-sensitive project: prioritize validation, least privilege, secrets management, tests, and auditability over rushing features.
