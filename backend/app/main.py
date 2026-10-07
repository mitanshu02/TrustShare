import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.activity import router as activity_router
from app.api.routes.admin import router as admin_router
from app.api.routes.audit_log import router as audit_log_router
from app.api.routes.auth import router as auth_router
from app.api.routes.files import router as files_router
from app.api.routes.folders import router as folders_router
from app.api.routes.share_links import router as share_links_router
from app.api.routes.stats import router as stats_router
from app.api.routes.monitoring import router as monitoring_router
from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="TrustShare API", lifespan=lifespan)

# Local dev origin is always allowed. The deployed frontend's origin is
# added via FRONTEND_URL so the live site works without hardcoding a
# URL that doesn't exist until Render assigns it — set this env var on
# Render once you know your frontend's real URL (e.g.
# https://trustshare-frontend-xxxx.onrender.com, no trailing slash).
allowed_origins = ["http://localhost:5173"]
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(folders_router)
app.include_router(files_router)
app.include_router(activity_router)
app.include_router(stats_router)
app.include_router(admin_router)
app.include_router(share_links_router)
app.include_router(monitoring_router)
app.include_router(audit_log_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "TrustShare backend is running"}