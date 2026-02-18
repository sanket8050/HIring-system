"""Application configuration."""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    """Application settings from environment variables."""

    mongo_uri: str = "mongodb+srv://jadhavsushant379_db_user:EjRiiekC4N1iZHg5@cluster0.f4zpb4k.mongodb.net/"
    database_name: str = "recruitment_db"
    collection_name: str = "candidates"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
