from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from .database import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    sector = Column(String(50), index=True)  # 반도체, AI 등
    sentiment_score = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True)      # 예: AAPL, 005930.KS
    price = Column(Float)                        # 현재가 또는 종가
    change_percent = Column(Float)               # 등락률
    date = Column(DateTime, default=datetime.utcnow)