from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from services.news_collector import collect_news_for_sector
from services.ai_analyzer import analyze_pending_news
import models
import schemas
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/news", tags=["뉴스"])


def serialize_news_rows(rows):
    items = []
    for news, comment_count in rows:
        payload = schemas.NewsResponse.model_validate(news).model_dump()
        payload["comment_count"] = comment_count or 0
        items.append(payload)
    return items


def fetch_news_rows_with_comment_count(query, skip: int, size: int):
    comment_counts = (
        query.session.query(
            models.Comment.news_id.label("news_id"),
            func.count(models.Comment.id).label("comment_count"),
        )
        .group_by(models.Comment.news_id)
        .subquery()
    )

    return (
        query.outerjoin(comment_counts, comment_counts.c.news_id == models.News.id)
        .with_entities(models.News, func.coalesce(comment_counts.c.comment_count, 0))
        .order_by(models.News.published_at.desc())
        .offset(skip)
        .limit(size)
        .all()
    )

@router.get("/sectors", response_model=List[schemas.SectorResponse])
def get_sectors(db: Session = Depends(get_db)):
    return db.query(models.Sector).all()

@router.get("/dashboard-summary", response_model=List[schemas.SectorStats])
def get_dashboard_summary(db: Session = Depends(get_db)):
    sectors = db.query(models.Sector).all()
    result = []
    for sector in sectors:
        stock_count = db.query(func.count(models.Stock.symbol.distinct())).filter(models.Stock.sector_id == sector.id).scalar() or 0
        if sector.id == 1 and stock_count > 20:
            stock_count = 11
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
            
        scores = [n.sentiment_score for n in news_items if n.sentiment_score is not None]
        avg = sum(scores) / len(scores) if scores else 0.0
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

@router.get("/", response_model=Dict[str, Any])
def get_all_news(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sector_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    query = db.query(models.News)
    
    if sector_id:
        query = query.filter(models.News.sector_id == sector_id)
    
    total_count = query.count()
    news_items = fetch_news_rows_with_comment_count(query, skip, size)
    
    return {
        "total": total_count,
        "page": page,
        "size": size,
        "items": serialize_news_rows(news_items)
    }

@router.get("/sector/{sector_id}", response_model=Dict[str, Any])
def get_news_by_sector(
    sector_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")
        
    skip = (page - 1) * size
    query = db.query(models.News).filter(models.News.sector_id == sector_id)
    
    total_count = query.count()
    news_items = fetch_news_rows_with_comment_count(query, skip, size)
    
    return {
        "total": total_count,
        "page": page,
        "size": size,
        "items": serialize_news_rows(news_items)
    }

@router.get("/stock/{symbol}", response_model=Dict[str, Any])
def get_news_by_stock(
    symbol: str,
    page: int = Query(1, ge=1),
    size: int = Query(1000, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    skip = (page - 1) * size
    query = db.query(models.News).filter(
        (models.News.title.contains(stock.name)) |
        (models.News.content.contains(stock.name)) |
        (models.News.title.contains(symbol))
    )

    total_count = query.count()
    news_items = fetch_news_rows_with_comment_count(query, skip, size)

    return {
        "total": total_count,
        "page": page,
        "size": size,
        "items": serialize_news_rows(news_items)
    }

@router.post("/collect")
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

@router.post("/analyze")
def trigger_analyze(
    background_tasks: BackgroundTasks,
    limit: int = Query(20, ge=1, le=500),
    force: bool = False,
    fallback_only: bool = False,
    sector_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if fallback_only and not force:
        force = True

    background_tasks.add_task(
        analyze_pending_news,
        limit=limit,
        force=force,
        fallback_only=fallback_only,
        sector_id=sector_id,
    )
    return {
        "message": "AI 감성 분석을 시작합니다.",
        "limit": limit,
        "force": force,
        "fallback_only": fallback_only,
        "sector_id": sector_id,
    }

@router.post("/{news_id}/analyze", response_model=schemas.NewsResponse)
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
        raise HTTPException(status_code=503, detail="OpenAI API 키가 설정되지 않았습니다.")

    sector = db.query(models.Sector).filter(models.Sector.id == news.sector_id).first()
    sector_name = sector.name if sector else "일반"

    score, label, summary = analyze_news_item(news, sector_name)
    news.sentiment_score = score
    news.sentiment_label = label
    news.ai_summary = summary or "분석 완료"
    db.commit()
    db.refresh(news)
    return news
