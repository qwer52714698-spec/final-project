import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# .env에서 주소 가져오기
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Supabase(PostgreSQL) 연결 엔진 설정
# pool_pre_ping=True는 연결이 끊겼는지 미리 확인하는 안전장치입니다.
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