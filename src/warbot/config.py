"""Configuration management for warbot."""

from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


DEFAULT_MODEL = "gpt-5-mini"
API_KEY_ENV_VARS = ("OPENAI_API_KEY", "OPENAI_APIKEY")


@dataclass
class Settings:
    """Runtime settings for the bot."""

    api_key: str
    model: str = DEFAULT_MODEL
    base_url: Optional[str] = None


def _get_api_key() -> Optional[str]:
    for key in API_KEY_ENV_VARS:
        value = os.getenv(key)
        if value:
            return value
    return None


def load_settings() -> Settings:
    """Load settings from environment and .env file."""
    load_dotenv()
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY in environment or .env file."
        )

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL")
    return Settings(api_key=api_key, model=model, base_url=base_url)


def build_client(settings: Settings) -> OpenAI:
    """Build an OpenAI client using provided settings."""
    if settings.base_url:
        return OpenAI(api_key=settings.api_key, base_url=settings.base_url)
    return OpenAI(api_key=settings.api_key)


