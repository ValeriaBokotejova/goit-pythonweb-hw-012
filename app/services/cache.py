import datetime
import json

import redis.asyncio as redis

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
    await redis_client.set(key, json.dumps(data, cls=EnhancedJSONEncoder), ex=ttl)


async def get_cached_contacts(user_id: int) -> list[dict] | None:
    key = f"contacts:user:{user_id}"
    raw = await redis_client.get(key)
    if raw:
        return json.loads(raw)
    return None


async def invalidate_contacts_cache(user_id: int):
    key = f"contacts:user:{user_id}"
    await redis_client.delete(key)


# ---------- BIRTHDAYS ----------


async def cache_birthdays(user_id: int, data: list[dict], ttl: int = 300):
    key = f"birthdays:user:{user_id}"
    await redis_client.set(key, json.dumps(data, cls=EnhancedJSONEncoder), ex=ttl)


async def get_cached_birthdays(user_id: int) -> list[dict] | None:
    key = f"birthdays:user:{user_id}"
    raw = await redis_client.get(key)
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
    await redis_client.set(key, json.dumps(data, cls=EnhancedJSONEncoder), ex=ttl)


async def get_cached_search_results(user_id: int, query: str) -> list[dict] | None:
    key = f"search:user:{user_id}:{query.lower()}"
    raw = await redis_client.get(key)
    if raw:
        return json.loads(raw)
    return None
