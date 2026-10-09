"""Settings, read once from environment variables when the service starts."""

import os

# Where the orders service listens
ORDERS_URL = os.environ.get("ORDERS_URL", "http://localhost:8001")

# How long to wait for orders before giving up, in seconds
DOWNSTREAM_TIMEOUT_SECONDS = float(os.environ.get("DOWNSTREAM_TIMEOUT_SECONDS", "5"))
