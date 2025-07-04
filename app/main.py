import os

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter

from app.routers import auth, contacts, users

app = FastAPI()


@app.on_event("startup")
async def startup():
    redis_client = redis.from_url(
        "redis://redis:6379",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_client)


# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join("app", "static", "favicon.ico"))


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}


app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
