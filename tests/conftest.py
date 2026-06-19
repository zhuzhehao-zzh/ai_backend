"""Test configuration — set env vars before any application imports."""

import os

# Set dummy API key + base URL so the LLM client can be instantiated
# at import time.  Real calls are mocked in individual test classes.
os.environ.setdefault("MOONSHOT_API_KEY", "test-skip-key")
os.environ.setdefault("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
