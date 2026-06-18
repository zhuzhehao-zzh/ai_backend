"""AI Backend - FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="AI Backend", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "AI Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
