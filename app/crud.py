from sqlalchemy.orm import Session
from . import models, schemas
import json

# 1. 뉴스 데이터 저장 (AI 분석 결과 포함 버전)
def create_news_with_analysis(db: Session, news_data: dict, analysis_result):
    """
    news_data: 수집기(collector)가 가져온 기본 뉴스 정보
    analysis_result: AI 팀원이 만든 AnalysisResult 객체
    """
    db_news = models.News(
        title=news_data.get("title"),
        content=news_data.get("content"),
        url=news_data.get("url"),
        publisher=news_data.get("publisher"),
        published_at=news_data.get("published_at"),
        
        # AI 분석 결과 매핑
        sentiment_label=analysis_result.sentiment_label,
        sentiment_score=analysis_result.sentiment_score,
        impact_score=analysis_result.impact_score,
        sector=analysis_result.sector,
        event_type=analysis_result.event_type,
        summary=analysis_result.summary,
        # 리스트 형태인 키워드를 문자열(JSON)로 변환하여 저장
        keywords=json.dumps(analysis_result.keywords, ensure_ascii=False)
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

# 2. 최신 뉴스 목록 조회 (필요 시 검색 필터 추가 가능)
def get_news_list(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.News).order_by(models.News.published_at.desc()).offset(skip).limit(limit).all()

# 3. 특정 섹터별 뉴스 모아보기 (AI 분석 결과 활용)
def get_news_by_sector(db: Session, sector: str):
    return db.query(models.News).filter(models.News.sector == sector).all()