from collections import defaultdict
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
from services.ai_analyzer import preprocess_news, normalize_event_type, normalize_impact_score

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


MANUAL_STOCK_ALIASES: dict[str, list[str]] = {
    "삼성전자": ["삼전"],
    "SK하이닉스": ["하이닉스"],
    "카카오뱅크": ["카뱅"],
    "현대차": ["현대자동차"],
    "POSCO홀딩스": ["포스코홀딩스", "포스코"],
    "LG에너지솔루션": ["엘지에너지솔루션", "LG엔솔", "엘지엔솔"],
}


def _normalize_text(text: str) -> str:
    return (text or "").replace(" ", "").lower()


def _build_stock_aliases(stock: models.Stock) -> list[str]:
    aliases = {stock.name or "", (stock.symbol or "").split(".")[0]}
    aliases.update(MANUAL_STOCK_ALIASES.get(stock.name or "", []))
    normalized = {_normalize_text(alias) for alias in aliases if alias}
    return sorted(alias for alias in normalized if alias)


def _iter_matching_stocks(stocks: Iterable[models.Stock], text: str) -> list[schemas.StockNewsMatch]:
    normalized_text = _normalize_text(text)
    matches: list[schemas.StockNewsMatch] = []

    for stock in stocks:
        aliases = _build_stock_aliases(stock)
        if not aliases:
            continue

        matched_alias = next((alias for alias in aliases if alias and alias in normalized_text), None)
        if not matched_alias:
            continue

        if matched_alias == _normalize_text(stock.name or ""):
            match_type = "name"
            confidence = 0.95
        elif matched_alias == _normalize_text((stock.symbol or "").split(".")[0]):
            match_type = "symbol"
            confidence = 0.85
        else:
            match_type = "alias"
            confidence = 0.8

        matches.append(
            schemas.StockNewsMatch(
                stock_id=stock.id,
                symbol=stock.symbol,
                stock_name=stock.name or stock.symbol,
                match_type=match_type,
                confidence=confidence,
            )
        )

    return matches


def match_related_stocks(db: Session, title: str, content: str | None = None, sector_id: int | None = None) -> list[schemas.StockNewsMatch]:
    """
    뉴스 제목/본문에서 종목명 또는 alias를 찾아 관련 종목 목록을 반환합니다.
    아직 매핑 테이블이 없으므로 규칙 기반 초안 함수로 사용합니다.
    """
    combined_text = " ".join(part for part in [title or "", content or ""] if part).strip()
    query = db.query(models.Stock)
    if sector_id is not None:
        query = query.filter(models.Stock.sector_id == sector_id)
    stocks = query.all()
    return _iter_matching_stocks(stocks, combined_text)


def build_daily_stock_news_features(
    db: Session,
    stock_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[schemas.DailyStockNewsFeature]:
    """
    종목과 관련된 뉴스만 모아 일자별 feature를 집계합니다.
    현재는 news_stock_map이 없으므로 규칙 기반 매칭으로 계산합니다.
    """
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        return []

    news_items = (
        db.query(models.News)
        .filter(models.News.published_at >= start_date, models.News.published_at <= end_date)
        .order_by(models.News.published_at.asc())
        .all()
    )

    buckets: dict[datetime, dict] = {}
    target_name = stock.name or stock.symbol

    for news in news_items:
        matches = match_related_stocks(db, news.title or "", news.content, sector_id=news.sector_id)
        if not any(match.stock_id == stock_id for match in matches):
            continue

        if not news.published_at:
            continue

        bucket_date = news.published_at.replace(hour=0, minute=0, second=0, microsecond=0)
        bucket = buckets.setdefault(
            bucket_date,
            {
                "scores": [],
                "impacts": [],
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "event_type_counts": defaultdict(int),
                "news_count": 0,
            },
        )

        clean_text = preprocess_news(news.title or "", news.content or "")
        score = float(news.sentiment_score or 0.0)
        label = (news.sentiment_label or "neutral").lower()
        event_type = normalize_event_type(None, news.title or "", clean_text)
        impact_score = normalize_impact_score(None, score, clean_text, event_type)

        bucket["scores"].append(score)
        bucket["impacts"].append(impact_score)
        bucket["event_type_counts"][event_type] += 1
        bucket["news_count"] += 1

        if label == "positive":
            bucket["positive_count"] += 1
        elif label == "negative":
            bucket["negative_count"] += 1
        else:
            bucket["neutral_count"] += 1

    features: list[schemas.DailyStockNewsFeature] = []
    for bucket_date in sorted(buckets.keys()):
        bucket = buckets[bucket_date]
        avg_sentiment = sum(bucket["scores"]) / len(bucket["scores"]) if bucket["scores"] else 0.0
        avg_impact = sum(bucket["impacts"]) / len(bucket["impacts"]) if bucket["impacts"] else 0.0
        features.append(
            schemas.DailyStockNewsFeature(
                date=bucket_date,
                stock_id=stock.id,
                symbol=stock.symbol,
                stock_name=target_name,
                news_count=bucket["news_count"],
                avg_sentiment_score=round(avg_sentiment, 3),
                avg_impact_score=round(avg_impact, 3),
                positive_count=bucket["positive_count"],
                negative_count=bucket["negative_count"],
                neutral_count=bucket["neutral_count"],
                event_type_counts=dict(bucket["event_type_counts"]),
            )
        )

    return features
