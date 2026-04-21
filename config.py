from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required — startup fails if missing
    MONGODB_URI: str
    PORT: int
    CLIENT_ORIGIN: str
    SESSION_TOKEN_SECRET: str
    ADMIN_API_KEY_HASH: str

    # Optional
    LOG_LEVEL: str = "info"
    LOG_DIR: str = "./logs"
    FORCE_HTTPS: bool = False
    SNIES_BASE_URL: str = "https://snies.mineducacion.gov.co"
    OLE_BASE_URL: str = "https://ole.mineducacion.gov.co"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
