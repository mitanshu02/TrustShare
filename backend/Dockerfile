# TrustShare backend — FastAPI + SQLAlchemy + Alembic
#
# Build:  docker build -t trustshare-backend .
# Run:    docker run -p 8000:8000 --env-file ../.env trustshare-backend
#
# In production (Render), the platform sets $PORT itself — do not
# hardcode a port. The container must bind to 0.0.0.0, not 127.0.0.1,
# or Render's load balancer can't reach it.

FROM python:3.12-slim

WORKDIR /app

# System deps: psycopg (PostgreSQL) needs libpq; keep the image slim by
# not installing build toolchains beyond what compiling psycopg needs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render (and most platforms) inject PORT at runtime; 8000 is only the
# local-dev fallback. Shell form (not exec/JSON form) is required here
# so ${PORT} actually gets expanded — exec form does not invoke a shell.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
