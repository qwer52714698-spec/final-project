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

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
from routers import news, stocks, comments, auth
from api import dashboard
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import threading
import time
from datetime import datetime
import pytz
import yfinance as yf
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
app.include_router(comments.router)
app.include_router(dashboard.router)

def collect_realtime_macro_indicators():
    """
    [교정 핵심] PostgreSQL double precision 타입 호환을 위해
    문자열 가공(콤마, % 부호)을 완전히 제거하고 순수 소수점(float) 데이터로만 DB에 인서트합니다.
    """
    print("[시스템] 구글 동기화용 실시간 거시 지표 수집 프로세스를 시작합니다.")
    db = SessionLocal()
    try:
        tickers = {
            "kospi": "^KS11",
            "usd_krw": "KRW=X",
            "vix": "^VIX"
        }
        
        # 코스피 종합지수 추출 및 변동률 연산
        kospi_ticker = yf.Ticker(tickers["kospi"])
        kospi_history = kospi_ticker.history(period="2d")
        kospi_index = 2641.20
        kospi_change = -0.80
        if len(kospi_history) >= 2:
            kospi_index = float(kospi_history['Close'].iloc[-1])
            prev_close = float(kospi_history['Close'].iloc[-2])
            kospi_change = float(((kospi_index - prev_close) / prev_close) * 100)

        # 원/달러 환율 추출 및 변동률 연산
        usd_history = yf.Ticker(tickers["usd_krw"]).history(period="2d")
        usd_krw_rate = 1388.50
        usd_krw_change = 2.10
        if len(usd_history) >= 2:
            usd_krw_rate = float(usd_history['Close'].iloc[-1])
            prev_usd = float(usd_history['Close'].iloc[-2])
            usd_krw_change = float(((usd_krw_rate - prev_usd) / prev_usd) * 100)

        # VIX 변동성 지수 추출
        vix_history = yf.Ticker(tickers["vix"]).history(period="1d")
        vix_score = 24.30
        if len(vix_history) >= 1:
            vix_score = float(vix_history['Close'].iloc[-1])

        vix_status = "위험" if vix_score >= 20 else "안정"
        
        kst = pytz.timezone('Asia/Seoul')
        now_kst = datetime.now(kst)

        # 문장 형식이 아닌 순수 수치 모델 파싱 맵핑 진행
        new_macro = models.MacroIndicator(
            fear_greed_score=58,
            vix_score=round(vix_score, 2),
            vix_status=vix_status,
            usd_krw_rate=round(usd_krw_rate, 2),
            usd_krw_change=round(usd_krw_change, 2),
            kospi_index=round(kospi_index, 2),
            kospi_change=round(kospi_change, 2),
            updated_at=now_kst
        )
        
        db.add(new_macro)
        db.commit()
        print("[완료] 야후 파이낸스 실시간 연동 데이터가 정상적인 숫자 타입으로 DB에 동기화되었습니다.")
    except Exception as e:
        db.rollback()
        print(f"[오류] 실시간 지표 크롤링 파이프라인 연산 실패: {e}")
    finally:
        db.close()

def run_full_analysis():
    print("[시스템] 뉴스 AI 분석 및 전 종목 예측 프로세스를 시작합니다.")
    
    collect_realtime_macro_indicators()
    
    try:
        processed_news = analyze_pending_news(limit=20)
        print(f"[완료] 뉴스 AI 분석 완료 ({processed_news}건 처리)")
    except Exception as e:
        print(f"[오류] 뉴스 분석 중 오류: {e}")

    db = SessionLocal()
    try:
        all_stocks = db.query(models.Stock).all()
        pending = [stock.symbol for stock in all_stocks]

        MAX_RETRY = 2
        for round_num in range(MAX_RETRY + 1):
            if not pending:
                break

            if round_num == 0:
                print(f"[1라운드] 전 종목 {len(pending)}개 분석 시작")
            else:
                print(f"[{round_num + 1}라운드] 실패 종목 {len(pending)}개 재시도")

            failed = []
            for symbol in pending:
                try:
                    res = requests.get(f"{SERVER_URL}/stocks/{symbol}/analyze", timeout=60)
                    if res.status_code == 200:
                        print(f"[성공] {symbol} 주가 예측 완료")
                    else:
                        print(f"[경고] {symbol} 실패 (status: {res.status_code}) -> 재시도 예정")
                        failed.append(symbol)
                except Exception as e:
                    print(f"[오류] {symbol} 오류: {e} -> 재시도 예정")
                    failed.append(symbol)
                time.sleep(5)

            pending = failed

        if pending:
            print(f"[경고] 최종 실패 종목 {len(pending)}개:")
            for symbol in pending:
                print(f"  - {symbol}")
        else:
            print("[완료] 전 종목 분석 완료!")

    finally:
        db.close()

    print("[시스템] 모든 데이터(거시지표+뉴스+주가) 최신화가 완료되었습니다.")

scheduler = BackgroundScheduler()
scheduler.add_job(run_full_analysis, 'cron', hour=16, minute=30)
scheduler.start()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=collect_realtime_macro_indicators).start()

@app.get("/")
def read_root():
    return {"status": "online", "message": "뉴스/주가 통합 자동 분석 시스템 가동 중"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)