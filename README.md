# TrustShare

**Secure File-Sharing & Digital Collaboration Platform**

TrustShare is a web platform for uploading, storing, and sharing files with server-side AES-256 encryption, fine-grained access control, and a full security audit trail. Built as part of the Infosys Springboard Virtual Internship program.

🔗 **Live demo:** [https://trustshare-v1.onrender.com]
📂 **Repository:** [github.com/mitanshu02/TrustShare](https://github.com/mitanshu02/TrustShare)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Security Notes](#security-notes)
- [Known Limitations & Future Scope](#known-limitations--future-scope)
- [Team & Acknowledgments](#team--acknowledgments)
- [License](#license)

---

## Overview

Most everyday file-sharing — email attachments, chat uploads, plain links — was never built with security in mind: files sit unencrypted, links never expire, and there's no record of who accessed what. TrustShare solves this with encryption-by-default storage, revocable and expiring share links, and a complete, searchable audit trail of every action taken on a file.

It's built for organizations, educational institutions, and teams that need to exchange sensitive documents — contracts, academic records, medical reports — without giving up visibility or control after the file leaves their hands.

## Key Features

**Authentication & Access Control**
- JWT-based authentication with bcrypt password hashing
- Role-based access control (admin/user) with step-up confirmation on role changes and an immutable role-change audit log
- OTP-based forgot/reset password flow

**File Management & Encryption**
- AES-256-GCM encryption, with a unique key generated per file
- Encryption keys isolated in their own table, never exposed via the API
- On-demand key rotation with a safe atomic key/ciphertext swap
- Encrypted file storage on Backblaze B2 (S3-compatible)

**Sharing**
- Direct, email-based sharing with view/download permission levels
- Public share links with configurable expiry, download limits, and revocation

**Security Monitoring**
- Deduplicated suspicious-login detection (5+ failed attempts from one IP in 15 minutes), alerting both the account owner and admins
- Real-time in-app notifications with a live unread-count badge
- Searchable, filterable, CSV-exportable audit log
- Per-file activity reports and admin-level security/storage analytics
- Background scheduler for expiring-link reminders

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, SQLAlchemy, Alembic, Pydantic |
| **Frontend** | React, Vite, Axios |
| **Database** | PostgreSQL (hosted on [Neon](https://neon.tech), serverless) |
| **Object Storage** | Backblaze B2 (S3-compatible, via `boto3`) |
| **Auth & Security** | JWT, bcrypt, AES-256-GCM (`cryptography`) |
| **Scheduling** | APScheduler |
| **Testing** | pytest, moto (mocked S3) |
| **DevOps** | Docker, Render |

## Architecture

```mermaid
flowchart LR
    A[User<br/>Web Browser] --> B[React Frontend<br/>Vite]
    B --> C[FastAPI Backend<br/>Auth · Encryption · RBAC]
    C --> D[(PostgreSQL<br/>Metadata & Audit Log)]
    C --> E[(Backblaze B2<br/>Encrypted File Storage)]
```

Files are encrypted server-side before ever touching object storage. The database holds only metadata, permissions, and audit events — never file contents or plaintext encryption keys.

## Project Structure

```
trustshare/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers (auth, files, sharing, monitoring...)
│   │   ├── core/            # Config, security, encryption, storage client, scheduler
│   │   ├── crud/            # Database operations
│   │   ├── db/               # SQLAlchemy engine/session setup
│   │   ├── models/           # ORM models
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── alembic/versions/    # Database migrations
│   ├── tests/                # pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/               # API client functions
│   │   ├── components/        # Reusable UI components
│   │   ├── context/           # Auth context
│   │   ├── layouts/           # Dashboard layout (nav, notification bell)
│   │   └── pages/             # Route-level pages
│   └── Dockerfile
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- A PostgreSQL database (local, Docker, or a free [Neon](https://neon.tech) project)
- A Backblaze B2 bucket (or any S3-compatible storage)
- Docker (optional, for containerized setup)

### Clone the repository

```bash
git clone https://github.com/mitanshu02/TrustShare.git
cd TrustShare
```

### Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the **repository root** (see [Environment Variables](#environment-variables)), then run the database migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API is now live at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app is now live at `http://localhost:5173`.

### Running with Docker

```bash
docker compose up --build
```

This builds and runs both the backend (`localhost:8000`) and frontend (`localhost:5173`) in containers, using the same root `.env` file.

## Environment Variables

Set these in a `.env` file at the repository root (never commit this file):

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string, in the form `postgresql+psycopg://user:pass@host/db` |
| `JWT_SECRET_KEY` | Secret key for signing JWTs — generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `B2_KEY_ID` | Backblaze B2 application key ID |
| `B2_APPLICATION_KEY` | Backblaze B2 application key |
| `B2_BUCKET_NAME` | Name of the B2 bucket used for encrypted file storage |
| `B2_ENDPOINT_URL` | B2 bucket's S3-compatible endpoint URL |
| `FRONTEND_URL` | *(production only)* Deployed frontend URL, used to allow CORS requests from it |

Set `VITE_API_BASE_URL` in `frontend/.env` to point the frontend at your backend (e.g. `http://127.0.0.1:8000` locally).

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v
```

The suite runs against a real PostgreSQL database and a mocked S3 server (via `moto`), covering:

- AES-256-GCM encryption round-trip, wrong-key rejection, and ciphertext tamper detection
- Authentication and role-based access control
- Deduplicated suspicious-login detection and notification delivery
- Share-link expiry, revocation, and access-level enforcement

## API Documentation

Interactive, auto-generated API documentation (Swagger UI) is available at `/docs` on any running instance of the backend — for example, `http://127.0.0.1:8000/docs` locally or the live demo link above.

## Deployment

- **Backend:** containerized with Docker and deployed on [Render](https://render.com) as a Web Service. Database migrations run automatically on container start.
- **Frontend:** deployed on Render as a Static Site, built with `npm run build`.
- **Database:** [Neon](https://neon.tech) serverless PostgreSQL.
- **File storage:** Backblaze B2.

## Security Notes

- Files are encrypted server-side with AES-256-GCM before being written to object storage; plaintext never touches disk at rest.
- Each file has its own encryption key, stored in a dedicated table isolated from the rest of the schema and never returned by any API response.
- Share-link tokens are high-entropy and hashed with SHA-256 for direct database lookup (not bcrypt, since tokens — unlike passwords — are not guessable and need fast indexed lookup).
- Suspicious-login detection is deduplicated per IP per time window to avoid alert fatigue during an active attack.
- Every security-sensitive action (encryption, sharing, key rotation, role changes, login attempts) is written to an immutable audit log.

## Known Limitations & Future Scope

- **Email delivery:** OTPs and notifications are currently logged to the console in development rather than sent via a real email provider.
- **Multi-factor authentication:** no OAuth2/SSO integration yet.
- **Mobile support:** no dedicated mobile app or PWA.
- **Anomaly detection:** suspicious-activity detection uses a fixed threshold rather than adaptive/ML-based detection.
- **Organization workspaces:** no team-level, folder-granular permission structure yet.
- **CI/CD:** no automated dependency/vulnerability scanning pipeline configured yet.

## Team & Acknowledgments

Built by Mitanshu as part of the **Infosys Springboard Virtual Internship** program.

