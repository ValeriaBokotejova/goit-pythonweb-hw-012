import os

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # JWT config
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    verify_token_expire_hours: int = 24

    # Admin
    admin_email: str
    admin_password: str

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Cloudinary
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    # Email config (SMTP)
    mail_username: EmailStr
    mail_password: str
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587

    # Frontend
    # frontend_base_url: str = "http://localhost:3000"
    frontend_verify_url: str = "http://localhost:8000/api/auth/verify-email"
    frontend_reset_url: str = "http://localhost:8000/api/auth/reset-password"

    # CORS
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()

if os.getenv("TESTING"):
    settings.database_url = "sqlite+aiosqlite:///:memory:"
