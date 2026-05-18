from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
from routers import news, stocks, comments, auth
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import threading
import time
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

    # 2. 전 종목 XGBoost 주가 분석 실행 (최대 3라운드 재시도)
    db = SessionLocal()
    try:
        all_stocks = db.query(models.Stock).all()
        pending = [stock.symbol for stock in all_stocks]  # 처음엔 전 종목

        MAX_RETRY = 2  # 최대 재시도 횟수 (총 3라운드)
        for round_num in range(MAX_RETRY + 1):
            if not pending:
                break

            if round_num == 0:
                print(f"🔄 [1라운드] 전 종목 {len(pending)}개 분석 시작")
            else:
                print(f"🔄 [{round_num + 1}라운드] 실패 종목 {len(pending)}개 재시도")

            failed = []  # 이번 라운드에서 실패한 종목 저장
            for symbol in pending:
                try:
                    res = requests.get(f"http://localhost:8000/stocks/{symbol}/analyze", timeout=60)
                    if res.status_code == 200:
                        print(f"✅ {symbol} 주가 예측 완료")
                    else:
                        print(f"⚠️ {symbol} 실패 (status: {res.status_code}) → 재시도 예정")
                        failed.append(symbol)
                except Exception as e:
                    print(f"❌ {symbol} 오류: {e} → 재시도 예정")
                    failed.append(symbol)
                time.sleep(10)  # yfinance Rate Limit 방지용 대기시간

            pending = failed  # 다음 라운드에서 실패한 것만 재시도

        if pending:
            print(f"⚠️ 최종 실패 종목 {len(pending)}개:")
            for symbol in pending:
                print(f"  - {symbol}")
        else:
            print("✅ 전 종목 분석 완료!")

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
    threading.Thread(target=start_initial_analysis, daemon=True).start()

@app.get("/")
def read_root():
    return {"status": "online", "message": "뉴스/주가 통합 자동 분석 시스템 가동 중"}