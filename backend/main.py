import sys
import os
from types import ModuleType
SERVER_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
fake_pkg_resources = ModuleType('pkg_resources')


def mock_resource_filename(package, resource):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_pykrx_dir = os.path.join(os.path.dirname(base_dir), '.venv', 'lib', 'python3.12', 'site-packages', 'pykrx')
    return os.path.join(venv_pykrx_dir, resource)

fake_pkg_resources.resource_filename = mock_resource_filename
fake_pkg_resources.declare_namespace = lambda name: None
fake_pkg_resources.get_distribution = lambda name: None

sys.modules['pkg_resources'] = fake_pkg_resources

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
from routers import news, stocks, comments, auth  # posts 제외
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import threading
import time
from services.ai_analyzer import analyze_pending_news

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
app.include_router(comments.router)  # 종목 토크방/뉴스 공용 댓글 적용 완료

def run_full_analysis():
    print("🚀 [시스템] 뉴스 AI 분석 및 전 종목 예측 프로세스를 시작합니다.")
    
    try:
        processed_news = analyze_pending_news(limit=20)
        print(f"✅ 뉴스 AI 분석 완료 ({processed_news}건 처리)")
    except Exception as e:
        print(f"❌ 뉴스 분석 중 오류: {e}")

    db = SessionLocal()
    try:
        all_stocks = db.query(models.Stock).all()
        pending = [stock.symbol for stock in all_stocks]

        MAX_RETRY = 2
        for round_num in range(MAX_RETRY + 1):
            if not pending:
                break

            if round_num == 0:
                print(f"🔄 [1라운드] 전 종목 {len(pending)}개 분석 시작")
            else:
                print(f"🔄 [{round_num + 1}라운드] 실패 종목 {len(pending)}개 재시도")

            failed = []
            for symbol in pending:
                try:
                    res = requests.get(f"{SERVER_URL}/stocks/{symbol}/analyze", timeout=60)
                    if res.status_code == 200:
                        print(f"✅ {symbol} 주가 예측 완료")
                    else:
                        print(f"⚠️ {symbol} 실패 (status: {res.status_code}) → 재시도 예정")
                        failed.append(symbol)
                except Exception as e:
                    print(f"❌ {symbol} 오류: {e} → 재시도 예정")
                    failed.append(symbol)
                time.sleep(5)

            pending = failed

        if pending:
            print(f"⚠️ 최종 실패 종목 {len(pending)}개:")
            for symbol in pending:
                print(f"  - {symbol}")
        else:
            print("✅ 전 종목 분석 완료!")

    finally:
        db.close()

    print("✨ [시스템] 모든 데이터(뉴스+주가) 최신화가 완료되었습니다.")

scheduler = BackgroundScheduler()
scheduler.add_job(run_full_analysis, 'cron', hour=16, minute=30)
scheduler.start()

@app.on_event("startup")
def startup_event():
    pass

@app.get("/")
def read_root():
    return {"status": "online", "message": "뉴스/주가 통합 자동 분석 시스템 가동 중"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)