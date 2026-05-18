from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/stock_trend_db")
    
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    NAVER_CLIENT_ID: str = os.environ.get("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.environ.get("NAVER_CLIENT_SECRET", "")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()