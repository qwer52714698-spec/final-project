from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 🟢 주석 해제 및 관계 설정: 유저가 삭제되면 쓴 댓글도 삭제되도록 설정
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
    # 🟢 추가: 뉴스를 조회할 때 달린 댓글들을 바로 가져올 수 있게 연결
    comments = relationship("Comment", back_populates="news", cascade="all, delete-orphan")


# 🆕 신규 추가: 댓글 모델
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 작성자 ID
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False) # 뉴스 ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 수정 시간 추가

    # 관계 설정
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