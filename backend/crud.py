from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
import json

# 1. 뉴스 데이터 저장 (팀원들의 models.News 구조에 맞게 수정)
def create_news_with_analysis(db: Session, news_data: dict, analysis_result):
    """
    팀원들의 News 모델은 sector_id(숫자)를 사용하며, 
    summary 대신 ai_summary라는 컬럼명을 사용합니다.
    """
    db_news = models.News(
        title=news_data.get("title"),
        content=news_data.get("content"),
        url=news_data.get("url"),
        published_at=news_data.get("published_at"),
        
        # 팀원들의 models.News 컬럼명에 맞게 매핑
        sector_id=news_data.get("sector_id"),  # 이제는 글자가 아니라 숫자 ID를 넣어야 함
        sentiment_label=analysis_result.get("sentiment_label"),
        sentiment_score=analysis_result.get("sentiment_score"),
        ai_summary=analysis_result.get("summary"), # summary -> ai_summary로 변경됨
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

# 2. 최신 뉴스 목록 조회
def get_news_list(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.News).order_by(models.News.published_at.desc()).offset(skip).limit(limit).all()

# 3. 특정 섹터별 뉴스 모아보기 (ID 기반 조회로 변경)
def get_news_by_sector(db: Session, sector_id: int):
    return db.query(models.News).filter(models.News.sector_id == sector_id).all()

# 4. 섹터별 통계 가져오기 (팀원들 news.py에서 활용하던 로직)
def get_sector_stats(db: Session):
    return db.query(
        models.Sector.name,
        func.count(models.News.id).label("news_count"),
        func.avg(models.News.sentiment_score).label("avg_sentiment")
    ).join(models.News).group_by(models.Sector.name).all()


def resolve_stock_by_symbol(db: Session, symbol: str):
    pure_symbol = symbol.split(".")[0]
    candidate_symbols = [pure_symbol, f"{pure_symbol}.KS", f"{pure_symbol}.KQ"]
    candidates = db.query(models.Stock).filter(models.Stock.symbol.in_(candidate_symbols)).all()
    if not candidates:
        return None

    preferred = [stock for stock in candidates if stock.name and not stock.name.startswith("Stock_")]
    for candidate_symbol in [pure_symbol, f"{pure_symbol}.KS", f"{pure_symbol}.KQ"]:
        for stock in preferred:
            if stock.symbol == candidate_symbol:
                return stock

    return preferred[0] if preferred else candidates[0]


def get_stored_daily_stock_news_features(
    db: Session,
    stock_id: int,
    start_date,
    end_date,
):
    return (
        db.query(models.DailyStockNewsFeature)
        .filter(
            models.DailyStockNewsFeature.stock_id == stock_id,
            models.DailyStockNewsFeature.date >= start_date.date(),
            models.DailyStockNewsFeature.date <= end_date.date(),
        )
        .order_by(models.DailyStockNewsFeature.date.asc())
        .all()
    )
