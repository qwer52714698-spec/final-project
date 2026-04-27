from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models
# DB 테이블 생성
models.Base.metadata.create_all(bind=engine)
# 1. FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="주식 트렌드 예측 에이전트 API",
    description="뉴스 감성 분석 및 XGBoost 기반 주가 예측 서비스",
    version="1.0.0"
)

# 2. CORS 설정 (프론트엔드 리액트와 연결하기 위해 필수!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # 리액트 기본 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 기본 테스트용 경로(Route) 설정
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "백엔드 서버가 성공적으로 가동되었습니다!",
        "version": "1.0.0"
    }

# 4. 나중에 여기에 뉴스, 주식, 회원가입 관련 경로를 추가할 예정