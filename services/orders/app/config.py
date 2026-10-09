"""Settings, read once from environment variables when the service starts.

The defaults suit a local run. In Compose every value is set explicitly.
"""

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://orders:orders@localhost:5432/orders"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PAYMENTS_URL = os.environ.get("PAYMENTS_URL", "http://localhost:8080")

# How long to wait for payments before giving up, in seconds.
# Shorter than the gateway's limit, so orders answers before the gateway stops waiting.
PAYMENTS_TIMEOUT_SECONDS = float(os.environ.get("PAYMENTS_TIMEOUT_SECONDS", "4"))

# How long a cached product list stays valid, in seconds
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "60"))

# How long to wait for Redis before treating the cache as unavailable, in seconds
CACHE_TIMEOUT_SECONDS = float(os.environ.get("CACHE_TIMEOUT_SECONDS", "0.2"))
