import os

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter

from app.core.config import settings
from app.middleware.cors import setup_cors
from app.routers import auth, contacts, users

app = FastAPI()


# ─────── Swagger ─────── #
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My FastAPI Project",
        version="1.0.0",
        description="API with cookie-based JWT authentication",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/login",
                    "scopes": {},
                },
            },
        },
    }

    for path in openapi_schema["paths"].values():
        for method in path:
            if "security" not in path[method]:
                path[method]["security"] = [{"OAuth2PasswordBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ───────────── Redis Limiter ───────────── #
@app.on_event("startup")
async def startup():
    redis_client = redis.from_url(
        f"redis://{settings.redis_host}:{settings.redis_port}",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_client)


# ───────────── CORS Middleware ───────────── #
setup_cors(app)

# ───────────── Static / Favicon ───────────── #
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join("app", "static", "favicon.ico"))


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}


# ───────────── Routers ───────────── #
app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
