from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal
import models, schemas
from dependencies import get_current_user

router = APIRouter(
    prefix="/news",
    tags=["comments"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. 댓글 작성 
@router.post("/{news_id}/comments", response_model=schemas.CommentResponse)
def create_comment(
    news_id: int, 
    comment: schemas.CommentCreate, 
    db: Session = Depends(get_db),
    # 🛡️ 여기서 로그인 여부를 검사하고 유저 정보를 가져옵니다
    current_user: models.User = Depends(get_current_user)
):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")
    
    new_comment = models.Comment(
        content=comment.content,
        news_id=news_id,
        user_id=current_user.id  #  고정값 1 대신 진짜 로그인한 유저 ID 삽입
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# 2. 특정 뉴스의 댓글 목록 조회 (조회는 로그인 안 해도 가능)
@router.get("/{news_id}/comments", response_model=List[schemas.CommentResponse])
def get_comments(news_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.news_id == news_id).all()
    return comments

# 3. 댓글 삭제 (본인만 삭제할 수 있게 보안 강화)
@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    
    if not db_comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    
    #  보안 체크
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인의 댓글만 삭제할 수 있습니다.")
    
    db.delete(db_comment)
    db.commit()
    return {"message": "댓글이 삭제되었습니다."}