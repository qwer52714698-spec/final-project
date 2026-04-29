from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
# 각 기능별 라우터 가져오기
from routers import news, stocks, auth 

# DB 테이블 생성 (서버 켤 때마다 모델 확인)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="주식 트렌드 예측 에이전트 API",
    description="뉴스 감성 분석 및 GPT-4o-mini 기반 주가 분석 서비스",
    version="1.0.0"
)

# CORS 설정: 리액트 포트(3000, 5173 등) 모두 허용하도록 넉넉히 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 개발 단계에서는 전체 허용이 편합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚦 분산되어 있던 기능(Router)들을 하나로 합체!
app.include_router(news.router)
app.include_router(stocks.router)
# app.include_router(auth.router) # auth.py가 준비되면 주석 해제

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "백엔드 서버가 성공적으로 가동되었습니다!",
        "engine": "GPT-4o-mini"
    }