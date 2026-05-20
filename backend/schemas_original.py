from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

# ── Sector ────────────────────────────────────────────────────────────────────

class SectorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]

    model_config = {"from_attributes": True}

class SectorStats(BaseModel):
    sector_id: int
    sector_name: str
    icon: Optional[str]
    stock_count: int
    news_count: int
    avg_sentiment: float
    sentiment_temperature: float
    positive_count: int
    negative_count: int
    neutral_count: int

# ── News ──────────────────────────────────────────────────────────────────────

class NewsResponse(BaseModel):
    id: int
    sector_id: int
    title: str
    content: Optional[str]
    url: Optional[str]
    published_at: Optional[datetime]
    sentiment_score: Optional[float] = 0.0
    sentiment_label: Optional[str] = "neutral"
    ai_summary: Optional[str]
    collected_at: datetime
    sector: Optional[SectorResponse]

    model_config = {"from_attributes": True}

# 🌟 조장님과 약속한 숫자 페이지네이션용 뉴스 응답 스키마 추가
class NewsListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[NewsResponse]

# ── Stock ─────────────────────────────────────────────────────────────────────

class StockResponse(BaseModel):
    id: int
    sector_id: int
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None

    model_config = {"from_attributes": True}

class StockPriceResponse(BaseModel):
    date: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None

    model_config = {"from_attributes": True}

class StockWithPrices(BaseModel):
    stock: StockResponse
    prices: List[StockPriceResponse]

# 🌟 XGBoost 3진 분류(상승/하락/횡보) 결과를 프론트엔드에 전달할 스키마 추가
class StockAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: str
    prediction: str            # "상승", "하락", "횡보"
    confidence: str            # "85.24%" 형태의 문자열
    top_influencers: Dict[str, float] # 핵심 영향 요인 Top 3
    analysis_date: str         # "2026-05-18"

# ── Post ──────────────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    title: str
    content: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostListItem(BaseModel):
    id: int
    title: str
    author_username: str
    views: int
    comment_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    views: int
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    comments: List["CommentResponse"] = []

    model_config = {"from_attributes": True}

class PostListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PostListItem]

# ── Comment ───────────────────────────────────────────────────────────────────

# 🌟 종목 토크방/뉴스 댓글에서도 공용으로 쓸 수 있도록 명시적 생성 스키마 설정
class CommentCreate(BaseModel):
    content: str
    post_id: Optional[int] = None
    news_id: Optional[int] = None
    stock_symbol: Optional[str] = None # 특정 주식 토크방용 필드 추가

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    post_id: Optional[int] = None
    news_id: Optional[int] = None
    stock_symbol: Optional[str] = None # 응답 시에도 종목 정보 포함 가능하도록 추가
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse # 수아님 설계대로 유저 객체가 통째로 들어가서 닉네임 파싱 가능!

    model_config = {"from_attributes": True}

# 관계 재빌드
PostResponse.model_rebuild()