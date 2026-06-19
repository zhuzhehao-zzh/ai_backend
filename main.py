"""AI Backend - FastAPI application entry point."""

import logging

from dotenv import load_dotenv

# Load .env BEFORE any modules that read env vars (especially the LLM client)
load_dotenv()

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
