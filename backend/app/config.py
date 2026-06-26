"""
ConnectAI Karnataka — Application Settings
Loads from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    app_name: str = "ConnectAI Karnataka"
    app_version: str = "1.0.0"
    debug: bool = False

    # ── Database ───────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://connectai:connectai@localhost:5432/connectai_karnataka",
        env="DATABASE_URL",
    )

    # ── API ────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "*",
    ]

    # ── AI ─────────────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")

    # ── Paths ──────────────────────────────────────────────────────────────
    data_dir: str = "./data"
    model_dir: str = "./models"

    # ── Karnataka spatial bounds ───────────────────────────────────────────
    karnataka_bbox: tuple[float, float, float, float] = (
        74.05, 11.59, 78.57, 18.45
    )  # (min_lon, min_lat, max_lon, max_lat)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
