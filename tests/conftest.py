"""Test configuration — set env vars before any application imports."""

import os

# Set a dummy API key so AsyncOpenAI() can be instantiated at import time.
# Real calls are mocked in individual test classes.
os.environ.setdefault("OPENAI_API_KEY", "test-skip-key")
