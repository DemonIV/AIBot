from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    SHOPIFY_STORE_URL: str
    SHOPIFY_ACCESS_TOKEN: str
    SHOPIFY_API_VERSION: str = "2024-01"
    GEMINI_API_KEY: str
    META_VERIFY_TOKEN: str = "CHANGE_ME"
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    META_GRAPH_API_VERSION: str = "v17.0"
    SOCIAL_MOCK_MODE: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("SHOPIFY_STORE_URL")
    @classmethod
    def validate_store_url(cls, v: str) -> str:
        if "http://" in v or "https://" in v:
            raise ValueError("SHOPIFY_STORE_URL must not contain 'http://' or 'https://'")
        return v

settings = Settings()
