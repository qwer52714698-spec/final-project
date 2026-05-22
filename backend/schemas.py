from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List, Dict, Any

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
    sentiment_score: Optional[float] = 0.0
    sentiment_label: Optional[str] = "neutral"
    ai_summary: Optional[str]
    collected_at: datetime
    sector: Optional[SectorResponse]
    comment_count: int = 0
    sentiment_explanation: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}

class NewsListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[NewsResponse]

class NewsSimple(BaseModel):
    id: int
    title: str
    sector_id: int
    sector: Optional[SectorResponse] = None

    model_config = {"from_attributes": True}

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

class CommentCreate(BaseModel):
    content: str
    post_id: Optional[int] = None
    news_id: Optional[int] = None
    stock_symbol: Optional[str] = None 

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    post_id: Optional[int] = None
    news_id: Optional[int] = None
    stock_symbol: Optional[str] = None 
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse 
    news: Optional[NewsSimple] = None

    model_config = {"from_attributes": True}

class MacroResponse(BaseModel):
    fear_greed_score: int
    vix_score: float
    vix_status: str
    usd_krw_rate: float
    usd_krw_change: float
    kospi_index: float
    kospi_change: float
    updated_at: datetime

    model_config = {"from_attributes": True}

class ScheduleResponse(BaseModel):
    id: int
    event_date: date
    category: str
    title: str
    d_day: int

    model_config = {"from_attributes": True}

class AnomalySignalResponse(BaseModel):
    id: int
    title: str
    description: str
    level: str

class SectorDetailResponse(BaseModel):
    sector_id: int
    sentiment_status: str
    foreigner_net_buy: float
    institutional_net_buy: float
    short_selling_ratio: float
    keywords: List[str]
    investment_tip: str

    model_config = {"from_attributes": True}

class DashboardTotalResponse(BaseModel):
    macro: MacroResponse
    anomalies: List[AnomalySignalResponse]
    schedules: List[ScheduleResponse]

PostResponse.model_rebuild()
