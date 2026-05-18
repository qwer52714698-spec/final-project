import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings 

raw_url = os.environ.get("DATABASE_URL")

if not raw_url or "localhost" in raw_url:
    db_user = os.environ.get("DB_USERNAME", "postgres")
    db_pass = os.environ.get("DB_PASSWORD", "password")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "stock_trend_db")
    
    if db_host == "localhost":
        SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
else:
    SQLALCHEMY_DATABASE_URL = raw_url

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