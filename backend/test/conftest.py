"""
Shared pytest fixtures.

Tests run against a real PostgreSQL database, not SQLite — the project's
own handoff notes already flag that SQLite doesn't preserve
timezone-aware datetimes or strict UUID typing the way Postgres does,
which caused false "bugs" during earlier manual testing. Using the real
engine avoids repeating that mistake here.

By default this points at a local throwaway database
(`trustshare_test` on localhost) so tests never touch the shared Neon
database. Override with TEST_DATABASE_URL if your setup differs, e.g.
to use Postgres running in Docker:

    TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost/trustshare_test pytest
"""

import os
import uuid

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://ts:ts@localhost/trustshare_test",
    ),
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("B2_KEY_ID", "test")
os.environ.setdefault("B2_APPLICATION_KEY", "test")
os.environ.setdefault("B2_BUCKET_NAME", "trustshare-test-bucket")
os.environ.setdefault("B2_ENDPOINT_URL", "http://127.0.0.1:5111")

import subprocess
import sys
import time
import urllib.request

import boto3
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app

MOTO_PORT = 5111
MOTO_URL = f"http://127.0.0.1:{MOTO_PORT}"


@pytest.fixture(scope="session", autouse=True)
def _mock_object_storage():
    """
    File uploads/downloads go through the real boto3 S3 client, which
    needs *something* on the other end of B2_ENDPOINT_URL. Rather than
    requiring a real Backblaze bucket (and real credentials) just to
    run the test suite, this spins up a local moto S3-mock server for
    the duration of the session — the same approach already verified
    to work against this codebase's exact storage.py client config.
    """
    process = subprocess.Popen(
        [sys.executable, "-m", "moto.server", "-p", str(MOTO_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            urllib.request.urlopen(MOTO_URL, timeout=0.5)
            break
        except OSError:
            time.sleep(0.2)
    else:
        process.terminate()
        raise RuntimeError("moto S3-mock server did not start in time")

    s3 = boto3.client(
        "s3",
        endpoint_url=MOTO_URL,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    s3.create_bucket(Bucket=os.environ["B2_BUCKET_NAME"])

    yield

    process.terminate()
    process.wait(timeout=5)

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Creates all tables once per test session, drops them at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """
    Truncates every table between tests so each test starts from an
    empty database, without paying the cost of recreating the schema
    each time.
    """
    yield
    with engine.connect() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("SET session_replication_role = 'origin'"))
        conn.commit()


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def unique_email():
    return f"test-{uuid.uuid4().hex[:10]}@example.com"