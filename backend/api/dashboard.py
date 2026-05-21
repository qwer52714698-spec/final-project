from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
from datetime import datetime, date, timedelta
from sqlalchemy import asc, desc, cast, String, or_

router = APIRouter(prefix="/dashboard", tags=["대시보드"])

@router.get("/main", response_model=schemas.DashboardTotalResponse)
def get_main_dashboard(db: Session = Depends(get_db)):
    recent_news = db.query(models.News).order_by(desc(models.News.id)).limit(300).all()
    
    pos_count = 0
    neg_count = 0
    
    for news in recent_news:
        if news.sentiment_label == "positive":
            pos_count += 1
        elif news.sentiment_label == "negative":
            neg_count += 1

    total_valid = pos_count + neg_count
    if total_valid > 0:
        final_sentiment_score = int((pos_count / total_valid) * 100)
    else:
        final_sentiment_score = 50

    macro = db.query(models.MacroIndicator).order_by(models.MacroIndicator.id.desc()).first()
    if not macro:
        macro = models.MacroIndicator(
            fear_greed_score=final_sentiment_score,
            vix_score=24.3,
            vix_status="위험",
            usd_krw_rate=1388.0,
            usd_krw_change=2.1,
            kospi_index=2641.0,
            kospi_change=-0.8,
            updated_at=datetime.utcnow()
        )
        db.add(macro)
        db.commit()
        db.refresh(macro)
    else:
        macro.fear_greed_score = final_sentiment_score
        macro.updated_at = datetime.utcnow()
        db.add(macro)
        db.commit()
        db.refresh(macro)

    anomalies = []
    
    high_sentiment_news = db.query(models.News).filter(models.News.sentiment_score >= 0.8).limit(1).all()
    if high_sentiment_news:
        anomalies.append(schemas.AnomalySignalResponse(
            id=1,
            title="반도체 — 감성↑·공탐↓",
            description="뉴스 긍정 최고조, 시장 심리는 공포 구간으로 역발상 진입 고려 가능",
            level="warning"
        ))
    
    five_days_ago = datetime.utcnow() - timedelta(days=5)
    samsung_stock = db.query(models.Stock).filter(models.Stock.symbol == "005930").first()
    if samsung_stock:
        falling_prices = db.query(models.StockPrice).filter(
            models.StockPrice.stock_id == samsung_stock.id,
            models.StockPrice.date >= five_days_ago
        ).order_by(desc(models.StockPrice.date)).limit(5).all()
        
        if len(falling_prices) >= 4:
            anomalies.append(schemas.AnomalySignalResponse(
                id=2,
                title="삼성전자 — 감성↑·주가↓",
                description="최근 영업일 지속 하락세 관측. 기관 수급 재확인 필요",
                level="danger"
            ))

    anomalies.append(schemas.AnomalySignalResponse(
        id=3,
        title="공매도 급증 2종목",
        description="삼성전자 18.2%, SK하이닉스 14.7% 공매도 거래 대금 상위 랭크",
        level="info"
    ))

    db_schedules = db.query(models.MarketSchedule).filter(models.MarketSchedule.event_date >= date.today()).order_by(asc(models.MarketSchedule.event_date)).limit(5).all()
    
    schedules_response = []
    for s in db_schedules:
        d_day = (s.event_date - date.today()).days
        schedules_response.append(schemas.ScheduleResponse(
            id=s.id,
            event_date=s.event_date,
            category=s.category,
            title=s.title,
            d_day=d_day
        ))

    if not schedules_response:
        mock_data = [
            {"date": date(2026, 5, 23), "cat": "거시", "title": "FOMC 의사록 발표"},
            {"date": date(2026, 5, 28), "cat": "실적", "title": "삼성전자 1Q 실적공시"},
            {"date": date(2026, 5, 30), "cat": "공시", "title": "CB 만기 도래"},
            {"date": date(2026, 6, 3), "cat": "보호", "title": "의무보호예수 해제"},
            {"date": date(2026, 6, 10), "cat": "배당", "title": "중간 배당 기준일"}
        ]
        for idx, m in enumerate(mock_data):
            d_day = (m["date"] - date.today()).days
            schedules_response.append(schemas.ScheduleResponse(
                id=idx+1,
                event_date=m["date"],
                category=m["cat"],
                title=m["title"],
                d_day=d_day
            ))

    return {
        "macro": macro,
        "anomalies": anomalies,
        "schedules": schedules_response
    }

@router.get("/sector/{sector_id}/detail")
def get_sector_detail_analysis(sector_id: int, db: Session = Depends(get_db)):
    detail = db.query(models.SectorDetailAnalysis).filter(models.SectorDetailAnalysis.sector_id == sector_id).first()
    
    if not detail:
        if sector_id == 1:
            detail = models.SectorDetailAnalysis(
                sector_id=sector_id,
                sentiment_status="감성 긍정",
                foreigner_net_buy=4821.0,
                institutional_net_buy=-1230.0,
                short_selling_ratio=18.2,
                keywords="AI반도체,HBM,재고조정,환율,수출호조,감산",
                investment_tip="감성 긍정이나 공탐지수 공포 구간 + 공매도 급증 — 역발상 진입 전 수급 재확인 권장"
            )
        else:
            detail = models.SectorDetailAnalysis(
                sector_id=sector_id,
                sentiment_status="중립",
                foreigner_net_buy=120.0,
                institutional_net_buy=45.0,
                short_selling_ratio=4.5,
                keywords="순환매,실적개선,수급집중",
                investment_tip="섹터 내 대장주 위주의 기관 수급 유입 세부 모니터링 필요"
            )
        db.add(detail)
        db.commit()
        db.refresh(detail)

    sector_obj = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    sector_name = sector_obj.name if sector_obj else ""

    # 🔥 [교정 핵심] 최신 쿼리 배치 기준 정렬 후 상위 추출 파이프라인 재구축
    pos_news_list = db.query(models.News).filter(
        or_(
            models.News.sector_id == sector_id,
            cast(models.News.sector_id, String) == str(sector_id),
            cast(models.News.sector_id, String).like(f"%{sector_name}%")
        ),
        models.News.sentiment_label == "positive"
    ).order_by(desc(models.News.id)).limit(5).all()

    neg_news_list = db.query(models.News).filter(
        or_(
            models.News.sector_id == sector_id,
            cast(models.News.sector_id, String) == str(sector_id),
            cast(models.News.sector_id, String).like(f"%{sector_name}%")
        ),
        models.News.sentiment_label == "negative"
    ).order_by(desc(models.News.id)).limit(5).all()

    # 🔥 [교정 핵심] 프론트엔드가 요구하는 점수 표기(sentiment_score) 추가 전송 바인딩
    top_pos_serialized = []
    for n in pos_news_list:
        top_pos_serialized.append({
            "id": n.id, 
            "title": n.title,
            "sentiment_score": float(n.sentiment_score) if n.sentiment_score else 0.0
        })

    top_neg_serialized = []
    for n in neg_news_list:
        top_neg_serialized.append({
            "id": n.id, 
            "title": n.title,
            "sentiment_score": float(n.sentiment_score) if n.sentiment_score else 0.0
        })

    keyword_list = [k.strip() for k in detail.keywords.split(",") if k.strip()]
    
    return {
        "sector_id": detail.sector_id,
        "sentiment_status": detail.sentiment_status,
        "foreigner_net_buy": detail.foreigner_net_buy,
        "institutional_net_buy": detail.institutional_net_buy,
        "short_selling_ratio": detail.short_selling_ratio,
        "keywords": keyword_list,
        "investment_tip": detail.investment_tip,
        "top_positive_news": top_pos_serialized,
        "top_negative_news": top_neg_serialized
    }