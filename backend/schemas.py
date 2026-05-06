from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    news_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
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
    sentiment_score: float
    sentiment_label: str
    ai_summary: Optional[str]
    collected_at: datetime
    sector: Optional[SectorResponse]

    model_config = {"from_attributes": True}


# ── Analysis (draft) ─────────────────────────────────────────────────────────

class AnalysisBase(BaseModel):
    news_id: int
    sentiment_score: float
    sentiment_label: str
    summary: str
    keywords: List[str] = Field(default_factory=list)
    event_type: Optional[str] = None
    impact_score: Optional[float] = None


class AnalysisCreate(AnalysisBase):
    pass


class AnalysisResponse(AnalysisBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Stock ─────────────────────────────────────────────────────────────────────

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

class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse

    model_config = {"from_attributes": True}


PostResponse.model_rebuild()
