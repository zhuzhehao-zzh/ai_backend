"""AI Backend - FastAPI application entry point."""

import logging

from fastapi import FastAPI

from routes.api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="AI Backend", version="0.1.0")

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "AI Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
