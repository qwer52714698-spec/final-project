from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DB 연결 정보 (Supabase 주소를 .env에 넣으시면 됩니다)
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/stock_trend_db"
    
    # 인증 관련
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # AI 및 API 키 (GEMINI 대신 OPENAI 사용)
    OPENAI_API_KEY: str = ""  # 변수명을 OPENAI_API_KEY로 변경
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()