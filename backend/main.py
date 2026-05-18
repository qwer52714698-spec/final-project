from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
import crud
from routers import news, stocks, comments, auth
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import threading
import time
from datetime import datetime, timedelta
from services.ai_analyzer import analyze_pending_news # 뉴스 분석 엔진 임포트

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="주식 트렌드 예측 에이전트 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(news.router)
app.include_router(stocks.router)
app.include_router(comments.router)

def run_full_analysis():
    print("🚀 [시스템] 뉴스 AI 분석 및 전 종목 예측 프로세스를 시작합니다.")
    
    # 1. 미처리 뉴스 GPT 분석 실행
    try:
        processed_news = analyze_pending_news(limit=20)
        print(f"✅ 뉴스 AI 분석 완료 ({processed_news}건 처리)")
    except Exception as e:
        print(f"❌ 뉴스 분석 중 오류: {e}")

    # 1.5 뉴스-종목 매핑 및 종목별 일자 뉴스 feature 사전 집계
    feature_db = SessionLocal()
    print("🧩 [시스템] 뉴스 feature 사전 집계를 시작합니다.")
    try:
        feature_stats = crud.refresh_news_feature_store(
            db=feature_db,
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now(),
        )
        print(
            "✅ 뉴스 feature 집계 완료 "
            f"(뉴스 {feature_stats['news_count']}건, "
            f"매칭 종목 {feature_stats['matched_stock_count']}개, "
            f"집계 행 {feature_stats['daily_feature_rows']}건)"
        )
    except Exception as e:
        feature_db.rollback()
        print(f"❌ 뉴스 feature 집계 중 오류: {e}")
    finally:
        feature_db.close()

    # 2. 전 종목 XGBoost 주가 분석 실행
    db = SessionLocal()
    try:
        all_stocks = db.query(models.Stock).all()
        print(f"📈 [시스템] 종목 예측 시작 ({len(all_stocks)}개 종목)")
        for stock in all_stocks:
            try:
                response = requests.get(f"http://localhost:8000/stocks/{stock.symbol}/analyze", timeout=60)
                if response.ok:
                    print(f"✅ {stock.symbol} 주가 예측 완료")
                else:
                    print(f"❌ {stock.symbol} 주가 예측 실패 (status={response.status_code})")
                time.sleep(1) 
            except Exception as e:
                print(f"❌ {stock.symbol} 분석 중 오류: {e}")
    finally:
        db.close()
    
    print("✨ [시스템] 모든 데이터(뉴스+주가) 최신화가 완료되었습니다.")

def start_initial_analysis():
    time.sleep(10) # 서버 안정화를 위해 10초 대기
    run_full_analysis()

scheduler = BackgroundScheduler()
scheduler.add_job(run_full_analysis, 'cron', hour=16, minute=30) # 장 마감 후 여유있게 4시 반 실행
scheduler.start()

@app.on_event("startup")
def startup_event():
    print("ℹ️ [시스템] startup 자동 전체 배치는 비활성화되었습니다.")

@app.get("/")
def read_root():
    return {"status": "online", "message": "뉴스/주가 통합 자동 분석 시스템 가동 중"}
