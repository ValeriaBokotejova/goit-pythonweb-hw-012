from fastapi_limiter.depends import RateLimiter

rate_limiter = RateLimiter(times=5, seconds=60)
