from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
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


# Analysis draft helpers
def build_analysis_payload(result) -> schemas.AnalysisCreate:
    return schemas.AnalysisCreate(
        news_id=result.news_id,
        sentiment_score=result.sentiment_score,
        sentiment_label=result.sentiment_label,
        summary=result.summary,
        keywords=getattr(result, "keywords", []) or [],
        event_type=getattr(result, "event_type", None),
        impact_score=getattr(result, "impact_score", None),
    )


def create_analysis(db: Session, analysis_data: schemas.AnalysisCreate):
    """
    Draft helper for future analysis-table migration.
    Runtime writes are intentionally disabled until models.Analysis is finalized.
    """
    if not hasattr(models, "Analysis"):
        raise RuntimeError("models.Analysis is not defined yet.")

    db_analysis = models.Analysis(
        news_id=analysis_data.news_id,
        sentiment_score=analysis_data.sentiment_score,
        sentiment_label=analysis_data.sentiment_label,
        summary=analysis_data.summary,
        keywords=json.dumps(analysis_data.keywords, ensure_ascii=False),
        event_type=analysis_data.event_type,
        impact_score=analysis_data.impact_score,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis_by_news_id(db: Session, news_id: int):
    if not hasattr(models, "Analysis"):
        raise RuntimeError("models.Analysis is not defined yet.")
    return db.query(models.Analysis).filter(models.Analysis.news_id == news_id).first()
