import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

if not SQLALCHEMY_DATABASE_URL or "localhost" in SQLALCHEMY_DATABASE_URL:
    if os.environ.get("RENDER"):
        db_user = os.environ.get("DB_USERNAME", "postgres")
        db_pass = os.environ.get("DB_PASSWORD")
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT", "6543")
        db_name = os.environ.get("DB_NAME", "postgres")
        
        if db_host and db_pass:
            SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL을 로컬 환경 변수나 렌더 설정에서 찾을 수 없습니다.")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()