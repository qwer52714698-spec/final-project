from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 뉴스를 생성할 때 필요한 데이터 규격
class NewsBase(BaseModel):
    title: str
    content: str
    url: str
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment_score: Optional[float] = 0.0

class NewsCreate(NewsBase):
    pass

# DB에서 뉴스를 읽어올 때의 데이터 규격 (ID와 생성일 포함)
class News(NewsBase):
    id: int

    class Config:
        from_attributes = True # SQLAlchemy 모델과 호환되게 설정