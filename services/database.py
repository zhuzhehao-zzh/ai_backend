"""Async MySQL connection pool and CRUD operations."""

import json
import os
import logging

import aiomysql

logger = logging.getLogger(__name__)

pool = None


async def init_pool():
    """Create the global connection pool (call once at startup)."""
    global pool
    pool = await aiomysql.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "aibackend"),
        password=os.getenv("DB_PASS", "Aibackend2024!"),
        db=os.getenv("DB_NAME", "ai_backend"),
        autocommit=True,
        maxsize=5,
    )
    logger.info("MySQL pool created")


async def close_pool():
    """Close the connection pool (call once at shutdown)."""
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("MySQL pool closed")


async def save_request(request_id: str, student_data: dict):
    """Store a student request."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO requests (request_id, student_data) VALUES (%s, %s)",
                (request_id, json.dumps(student_data, ensure_ascii=False)),
            )


async def save_response(
    response_id: str,
    request_id: str,
    report: dict,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
):
    """Store a model response linked to its request."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO responses (response_id, request_id, report, tokens_prompt, tokens_completion) VALUES (%s, %s, %s, %s, %s)",
                (
                    response_id,
                    request_id,
                    json.dumps(report, ensure_ascii=False),
                    prompt_tokens,
                    completion_tokens,
                ),
            )


async def save_feedback(response_id: str, rating: int, comment: str = None):
    """Store user feedback for a response."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO feedback (response_id, rating, comment) VALUES (%s, %s, %s)",
                (response_id, rating, comment),
            )
