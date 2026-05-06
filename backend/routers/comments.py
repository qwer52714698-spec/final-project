from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
import models, schemas  # schemas는 데이터 규격을 정의하는 파일입니다.

router = APIRouter(
    prefix="/news",
    tags=["comments"]
)

# DB 세션 연결 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. 댓글 작성 (Create)
@router.post("/{news_id}/comments", response_model=schemas.Comment)
def create_comment(news_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    # 뉴스가 실제로 존재하는지 먼저 확인
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
    
    # 댓글 객체 생성 (지금은 로그인 연동 전이라 임시로 user_id=1 부여)
    new_comment = models.Comment(
        content=comment.content,
        news_id=news_id,
        user_id=1  # TODO: JWT 연동 후 실제 로그인한 유저 ID로 변경 예정
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# 2. 특정 뉴스의 댓글 목록 조회 (Read)
@router.get("/{news_id}/comments", response_model=List[schemas.Comment])
def get_comments(news_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.news_id == news_id).all()
    return comments

# 3. 댓글 삭제 (Delete)
@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    
    db.delete(db_comment)
    db.commit()
    return {"message": "댓글이 삭제되었습니다."}