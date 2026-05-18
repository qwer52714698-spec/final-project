from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, BigInteger, JSON, Date, UniqueConstraint  # 💡 JSON 추가됨
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 유저가 삭제되면 쓴 댓글도 삭제되도록 설정
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    icon = Column(String(10), default="📊")

    news_items = relationship("News", back_populates="sector")
    stocks = relationship("Stock", back_populates="sector")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(2048), unique=True)
    published_at = Column(DateTime)
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default="neutral")
    ai_summary = Column(Text)
    collected_at = Column(DateTime, default=datetime.utcnow)

    sector = relationship("Sector", back_populates="news_items")
    comments = relationship("Comment", back_populates="news", cascade="all, delete-orphan")
    stock_matches = relationship("NewsStockMap", back_populates="news", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="comments")
    news = relationship("News", back_populates="comments")


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    symbol = Column(String(20), unique=True, nullable=False)
    name = Column(String(100))
    exchange = Column(String(20), default="KRX")

    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    sector = relationship("Sector", back_populates="stocks")
    # 💡 분석 결과와 주식 정보를 바로 연결할 수 있게 추가
    predictions = relationship("StockPrediction", back_populates="stock", cascade="all, delete-orphan")
    news_matches = relationship("NewsStockMap", back_populates="stock", cascade="all, delete-orphan")
    daily_news_features = relationship("DailyStockNewsFeature", back_populates="stock", cascade="all, delete-orphan")


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

    stock = relationship("Stock", back_populates="prices")


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id")) 
    ticker = Column(String)
    prediction = Column(String) # 상승 또는 하락
    confidence = Column(String) # 예: 75.5%
    accuracy = Column(String, nullable=True) # 분석 정확도
    important_factors = Column(JSON) 
    created_at = Column(DateTime, default=func.now())

    # 💡 Stock 모델과의 관계 정의
    stock = relationship("Stock", back_populates="predictions")


class NewsStockMap(Base):
    __tablename__ = "news_stock_map"
    __table_args__ = (
        UniqueConstraint("news_id", "stock_id", name="uq_news_stock_map_news_stock"),
    )

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    match_type = Column(String(20), nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    news = relationship("News", back_populates="stock_matches")
    stock = relationship("Stock", back_populates="news_matches")


class DailyStockNewsFeature(Base):
    __tablename__ = "daily_stock_news_features"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_daily_stock_news_features_stock_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    news_count = Column(Integer, default=0, nullable=False)
    avg_sentiment_score = Column(Float, default=0.0, nullable=False)
    avg_impact_score = Column(Float, default=0.0, nullable=False)
    positive_count = Column(Integer, default=0, nullable=False)
    negative_count = Column(Integer, default=0, nullable=False)
    neutral_count = Column(Integer, default=0, nullable=False)
    earnings_count = Column(Integer, default=0, nullable=False)
    policy_regulation_count = Column(Integer, default=0, nullable=False)
    supply_contract_count = Column(Integer, default=0, nullable=False)
    labor_legal_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    stock = relationship("Stock", back_populates="daily_news_features")
