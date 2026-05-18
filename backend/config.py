import os
from pydantic_settings import BaseSettings

raw_database_url = os.environ.get("DATABASE_URL")

if not raw_database_url and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                raw_database_url = line.split("DATABASE_URL=")[1].strip()

final_db_url = raw_database_url or "postgresql://postgres:password@localhost:5432/stock_trend_db"

class Settings(BaseSettings):
    DATABASE_URL: str = final_db_url
    
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    NAVER_CLIENT_ID: str = os.environ.get("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.environ.get("NAVER_CLIENT_SECRET", "")

settings = Settings()