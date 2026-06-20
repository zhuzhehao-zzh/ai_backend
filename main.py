"""AI Backend - FastAPI application entry point."""

import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# Load .env BEFORE any modules that read env vars (especially the LLM client)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router as api_router
from services.database import init_pool, close_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    """Initialize DB pool on app start."""
    try:
        await init_pool()
        logger.info("Database pool initialized")
    except Exception as e:
        logger.warning("Database pool init failed (non-fatal): %s", e)


@app.on_event("shutdown")
async def shutdown():
    """Close DB pool on app shutdown."""
    try:
        await close_pool()
        logger.info("Database pool closed")
    except Exception as e:
        logger.warning("Database pool close failed: %s", e)


@app.get("/")
async def root():
    return {"message": "AI Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEV", "").lower() in ("1", "true"),
    )
