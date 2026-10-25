"""The product cache in Redis.

The cache is an optimisation, never a requirement. Every method swallows a
Redis failure and reports "nothing cached", so the caller falls back to the
database and the request still succeeds.
"""

import json
import logging

import redis

from app import config

logger = logging.getLogger("orders.cache")

PRODUCTS_KEY = "products:all"


class ProductCache:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def get_products(self) -> list[dict] | None:
        """Return the cached product list, or None if it is missing or Redis is down."""
        try:
            cached = self._client.get(PRODUCTS_KEY)
        except redis.RedisError as error:
            logger.warning("cache read failed, using the database: %r", error)
            return None
        return json.loads(cached) if cached else None

    def set_products(self, products: list[dict]) -> None:
        """Store the product list for a limited time. A failure is logged and ignored."""
        try:
            self._client.set(
                PRODUCTS_KEY, json.dumps(products), ex=config.CACHE_TTL_SECONDS
            )
        except redis.RedisError as error:
            logger.warning("cache write failed: %r", error)


# Connecting is lazy: nothing is sent to Redis until the first command.
_cache = ProductCache(
    redis.Redis.from_url(
        config.REDIS_URL,
        socket_connect_timeout=config.CACHE_TIMEOUT_SECONDS,
        socket_timeout=config.CACHE_TIMEOUT_SECONDS,
        decode_responses=True,
    )
)


def get_cache() -> ProductCache:
    return _cache
