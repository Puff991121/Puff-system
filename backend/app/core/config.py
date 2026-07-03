from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    name: str = "Puff API"
    env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    secret_key: str = Field("development-only-secret-key-change-me", min_length=32)
    access_token_expire_minutes: int = Field(120, gt=0)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    admin_username: str = "admin"
    admin_password: str = "admin123"

    @property
    def docs_enabled(self) -> bool:
        return self.env != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
