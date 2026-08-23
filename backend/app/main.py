from fastapi import FastAPI

app = FastAPI(title="TrustShare API")


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "TrustShare backend is running"}