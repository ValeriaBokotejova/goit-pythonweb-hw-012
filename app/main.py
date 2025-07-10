import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter

from app.core.config import settings
from app.db.session import async_session, wait_for_db
from app.middleware.cors import setup_cors
from app.routers import auth, contacts, users
from app.services.admin import create_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context:
     1) wait for the database
     2) initialize the Redis‑backed rate limiter
     3) ensure an admin user exists
    """
    logger.info("⏳ Waiting for the database to be ready...")
    await wait_for_db()
    logger.info("✅ Database is ready!")

    try:
        redis_connection = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
        await FastAPILimiter.init(redis_connection)
        logger.info("✅ FastAPILimiter initialized")
    except Exception as e:
        logger.warning(f"⚠️ Skipping rate‑limiter init (Redis not available?): {e}")

    async with async_session() as db:
        """
        On startup, connect to the DB and create the admin user if it doesn’t exist.
        """
        logger.info("⚙️ Checking admin user…")
        await create_admin(db)

    yield


app = FastAPI(
    title="FastAPI Contacts API",
    description="An example contacts service with auth, rate‑limits, etc.",
    lifespan=lifespan,
)

setup_cors(app)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# serve Sphinx HTML docs under /docs-html
app.mount(
    "/docs-html",
    StaticFiles(directory="docs/build/html", html=True),
    name="docs_html",
)


@app.get("/", tags=["Root"])
async def root():
    """
    Health‑check / root endpoint.
    ---
    Returns:
        dict: { "message": "Welcome to FastAPI application!" }
    """
    return {"message": "Welcome to FastAPI application!"}


def custom_openapi():
    """
    Generate a custom OpenAPI schema that:
     - Includes OAuth2PasswordBearer globally
     - Uses our own title, version, description
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI Contacts API",
        version="1.0.0",
        description="Contact API",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/login",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access",
                    },
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
