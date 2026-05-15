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

# --- 섹터 관련 엔드포인트 ---

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

# --- 페이지네이션 적용된 뉴스 목록 엔드포인트 ---

@router.get("/", response_model=Dict[str, Any])
def get_all_news(
    page: int = Query(1, ge=1, description="현재 페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지당 뉴스 개수"),
    sector_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    숫자 페이지네이션을 지원하는 전체 뉴스 목록 API
    """
    skip = (page - 1) * size
    query = db.query(models.News)
    
    if sector_id:
        query = query.filter(models.News.sector_id == sector_id)
    
    # 1. 필터링된 전체 뉴스 개수 구하기
    total_count = query.count()
    
    # 2. 현재 페이지에 해당하는 데이터 가져오기
    news_items = (
        query.order_by(models.News.published_at.desc())
        .offset(skip)
        .limit(size)
        .all()
    )
    
    return {
        "total": total_count,
        "page": page,
        "size": size,
        "items": [schemas.NewsResponse.model_validate(n) for n in news_items]  # ✅ 직렬화 수정
    }

@router.get("/sector/{sector_id}", response_model=Dict[str, Any])
def get_news_by_sector(
    sector_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    섹터별 숫자 페이지네이션 뉴스 API
    """
    sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")
        
    skip = (page - 1) * size
    query = db.query(models.News).filter(models.News.sector_id == sector_id)
    
    total_count = query.count()
    news_items = (
        query.order_by(models.News.published_at.desc())
        .offset(skip)
        .limit(size)
        .all()
    )
    
    return {
        "total": total_count,
        "page": page,
        "size": size,
        "items": [schemas.NewsResponse.model_validate(n) for n in news_items]  # ✅ 직렬화 수정
    }

# --- 작업 트리거 및 분석 엔드포인트 ---

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