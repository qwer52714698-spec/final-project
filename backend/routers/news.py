from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from services.news_collector import collect_news_for_sector
from services.ai_analyzer import analyze_pending_news
import models
import schemas
from typing import List, Optional

router = APIRouter(prefix="/news", tags=["뉴스"])


@router.get("/sectors", response_model=List[schemas.SectorResponse])
def get_sectors(db: Session = Depends(get_db)):
    return db.query(models.Sector).all()


@router.get("/dashboard-summary", response_model=List[schemas.SectorStats])
def get_dashboard_summary(db: Session = Depends(get_db)):
    sectors = db.query(models.Sector).all()
    result = []
    for sector in sectors:
        stock_count = db.query(func.count(models.Stock.id)).filter(models.Stock.sector_id == sector.id).scalar() or 0
        news_items = db.query(models.News).filter(models.News.sector_id == sector.id).all()
        if not news_items:
            result.append(schemas.SectorStats(
                sector_id=sector.id,
                sector_name=sector.name,
                icon=sector.icon,
                stock_count=stock_count,
                news_count=0,
                avg_sentiment=0.0,
                sentiment_temperature=50.0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
            ))
            continue
        scores = [n.sentiment_score for n in news_items]
        avg = sum(scores) / len(scores)
        temperature = (avg + 1) / 2 * 100
        pos = sum(1 for n in news_items if n.sentiment_label == "positive")
        neg = sum(1 for n in news_items if n.sentiment_label == "negative")
        neu = sum(1 for n in news_items if n.sentiment_label == "neutral")
        result.append(schemas.SectorStats(
            sector_id=sector.id,
            sector_name=sector.name,
            icon=sector.icon,
            stock_count=stock_count,
            news_count=len(news_items),
            avg_sentiment=round(avg, 3),
            sentiment_temperature=round(temperature, 1),
            positive_count=pos,
            negative_count=neg,
            neutral_count=neu,
        ))
    return result


@router.get("/sector/{sector_id}", response_model=List[schemas.NewsResponse])
def get_news_by_sector(
    sector_id: int,
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")
    return (
        db.query(models.News)
        .filter(models.News.sector_id == sector_id)
        .order_by(models.News.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/", response_model=List[schemas.NewsResponse])
def get_all_news(
    limit: int = 30,
    skip: int = 0,
    sector_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.News)
    if sector_id:
        q = q.filter(models.News.sector_id == sector_id)
    return q.order_by(models.News.published_at.desc()).offset(skip).limit(limit).all()


@router.post("/collect", summary="뉴스 수집 트리거")
def trigger_collect(
    background_tasks: BackgroundTasks,
    sector_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if sector_id:
        sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
        if not sector:
            raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")
        background_tasks.add_task(collect_news_for_sector, sector.id, sector.name)
        return {"message": f"{sector.name} 뉴스 수집을 시작합니다."}
    sectors = db.query(models.Sector).all()
    for s in sectors:
        background_tasks.add_task(collect_news_for_sector, s.id, s.name)
    return {"message": "전체 섹터 뉴스 수집을 시작합니다."}


@router.post("/analyze", summary="AI 감성 분석 트리거")
def trigger_analyze(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(analyze_pending_news)
    return {"message": "AI 감성 분석을 시작합니다."}


@router.post("/{news_id}/analyze", response_model=schemas.NewsResponse, summary="개별 뉴스 AI 감성분석")
def analyze_single(
    news_id: int,
    db: Session = Depends(get_db),
):
    from config import settings
    from services.ai_analyzer import analyze_news_item

    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="Openai API 키가 설정되지 않았습니다.")

    sector = db.query(models.Sector).filter(models.Sector.id == news.sector_id).first()
    sector_name = sector.name if sector else "일반"

    score, label, summary = analyze_news_item(news, sector_name)
    news.sentiment_score = score
    news.sentiment_label = label
    news.ai_summary = summary or "분석 완료"
    db.commit()
    db.refresh(news)
    return news
