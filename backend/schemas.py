from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

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

class NewsResponse(BaseModel):
    id: int
    sector_id: int
    title: str
    content: Optional[str]
    url: Optional[str]
    published_at: Optional[datetime]
    sentiment_score: float
    sentiment_label: str
    ai_summary: Optional[str]
    collected_at: datetime
    sector: Optional[SectorResponse]

    model_config = {"from_attributes": True}

<<<<<<< HEAD
# ── Stock ─────────────────────────────────────────────────────────────────────
=======
class NewsListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[NewsResponse]
>>>>>>> ae3079b79facd70bbb615bdb03e1f781a968025a

class StockResponse(BaseModel):
    id: int
    sector_id: int
    symbol: str
    name: Optional[str]
    exchange: Optional[str]

    model_config = {"from_attributes": True}

class StockPriceResponse(BaseModel):
    date: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]

    model_config = {"from_attributes": True}

class StockWithPrices(BaseModel):
    stock: StockResponse
    prices: List[StockPriceResponse]

<<<<<<< HEAD
# ── Post ──────────────────────────────────────────────────────────────────────
=======
class StockAnalysisResponse(BaseModel):
    status: str = "success"
    symbol: Optional[str] = None
    prediction: str
    confidence: Optional[str] = None
    top_influencers: Dict[str, float]
    analysis_date: str
    actual_return: float
    predicted_return: float
    win_rate: float
    period_start: str
    period_end: str
>>>>>>> ae3079b79facd70bbb615bdb03e1f781a968025a

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

<<<<<<< HEAD
# ── Comment ───────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str
=======
class CommentCreate(BaseModel):
    content: str
    post_id: Optional[int] = None
    news_id: Optional[int] = None
    stock_symbol: Optional[str] = None 
>>>>>>> ae3079b79facd70bbb615bdb03e1f781a968025a

class CommentUpdate(BaseModel):
    content: str

# ✅ 마이페이지용 뉴스 간략 정보 (순환 참조 방지용)
class NewsSimple(BaseModel):
    id: int
    title: str
    sector_id: int
    sector: Optional[SectorResponse] = None

    model_config = {"from_attributes": True}

class CommentResponse(BaseModel):
    id: int
    post_id: Optional[int] = None
    news_id: Optional[int] = None
<<<<<<< HEAD
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    news: Optional[NewsSimple] = None  # ✅ 마이페이지 뉴스 정보용

    model_config = {"from_attributes": True}

PostResponse.model_rebuild()
=======
    stock_symbol: Optional[str] = None 
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse 

    model_config = {"from_attributes": True}

PostResponse.model_rebuild()
>>>>>>> ae3079b79facd70bbb615bdb03e1f781a968025a
