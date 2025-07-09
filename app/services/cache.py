import datetime
import json
import logging

import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True,
)


# Custom JSON encoder to handle datetime.date and datetime.datetime
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


# ---------- CONTACTS ----------


async def cache_contacts(user_id: int, data: list[dict], ttl: int = 60):
    key = f"contacts:user:{user_id}"
    try:
        await redis_client.set(
            key,
            json.dumps(data, cls=EnhancedJSONEncoder),
            ex=ttl,
        )
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip caching contacts for user {user_id}: {e}",
        )


async def get_cached_contacts(user_id: int) -> list[dict] | None:
    key = f"contacts:user:{user_id}"
    try:
        raw = await redis_client.get(key)
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip getting cached contacts for user {user_id}: {e}",
        )
        return None

    if raw:
        return json.loads(raw)
    return None


async def invalidate_contacts_cache(user_id: int):
    key = f"contacts:user:{user_id}"
    try:
        await redis_client.delete(key)
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip invalidating contacts cache for user {user_id}: {e}",
        )


# ---------- BIRTHDAYS ----------


async def cache_birthdays(user_id: int, data: list[dict], ttl: int = 300):
    key = f"birthdays:user:{user_id}"
    try:
        await redis_client.set(
            key,
            json.dumps(data, cls=EnhancedJSONEncoder),
            ex=ttl,
        )
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip caching birthdays for user {user_id}: {e}",
        )


async def get_cached_birthdays(user_id: int) -> list[dict] | None:
    key = f"birthdays:user:{user_id}"
    try:
        raw = await redis_client.get(key)
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip getting cached birthdays for user {user_id}: {e}",
        )
        return None

    if raw:
        return json.loads(raw)
    return None


# ---------- SEARCH ----------


async def cache_search_results(
    user_id: int,
    query: str,
    data: list[dict],
    ttl: int = 60,
):
    key = f"search:user:{user_id}:{query.lower()}"
    try:
        await redis_client.set(
            key,
            json.dumps(data, cls=EnhancedJSONEncoder),
            ex=ttl,
        )
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip caching search results for user {user_id}, query '{query}': {e}",
        )


async def get_cached_search_results(user_id: int, query: str) -> list[dict] | None:
    key = f"search:user:{user_id}:{query.lower()}"
    try:
        raw = await redis_client.get(key)
    except RedisError as e:
        logger.warning(
            f"Redis unavailable, skip getting cached search for user {user_id}, query '{query}': {e}",
        )
        return None

    if raw:
        return json.loads(raw)
    return None
