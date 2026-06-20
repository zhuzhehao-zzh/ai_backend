"""AI Backend - FastAPI application entry point."""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router as api_router
from services.database import init_pool, close_pool

# ── Logging setup ──────────────────────────────────────────────────
LOG_DIR = os.getenv("LOG_DIR", "/root/Desktop/career/log")
start_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

os.makedirs(f"{LOG_DIR}/db", exist_ok=True)

log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Main file handler
log_path = f"{LOG_DIR}/server-{start_ts}.log"
file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format))

# DB file handler
db_log_path = f"{LOG_DIR}/db/db-{start_ts}.log"
db_handler = logging.FileHandler(db_log_path, encoding="utf-8")
db_handler.setLevel(logging.INFO)
db_handler.setFormatter(logging.Formatter(log_format))

# Console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(log_format))

root = logging.getLogger()
root.setLevel(logging.INFO)
# Remove default handlers and add our own
root.handlers.clear()
root.addHandler(file_handler)
root.addHandler(console)

# Give the db logger its own file
db_logger = logging.getLogger("services.database")
db_logger.handlers.clear()
db_logger.addHandler(db_handler)
db_logger.addHandler(console)

logger = logging.getLogger(__name__)
logger.info("Logging to %s", log_path)

# ── App setup ──────────────────────────────────────────────────────

app = FastAPI(title="AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    try:
        await init_pool()
        logger.info("Database pool initialized")
    except Exception as e:
        logger.warning("Database pool init failed (non-fatal): %s", e)


@app.on_event("shutdown")
async def shutdown():
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
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEV", "").lower() in ("1", "true"),
    )
