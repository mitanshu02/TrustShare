from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.activity import router as activity_router
from app.api.routes.auth import router as auth_router
from app.api.routes.files import router as files_router
from app.api.routes.folders import router as folders_router
from app.api.routes.stats import router as stats_router

app = FastAPI(title="TrustShare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(folders_router)
app.include_router(files_router)
app.include_router(activity_router)
app.include_router(stats_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "TrustShare backend is running"}