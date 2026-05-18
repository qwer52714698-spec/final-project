from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
import models
import schemas
from typing import List
from datetime import datetime
router = APIRouter(tags=["댓글"])

# ── 1. 수아님 프론트 주소 대응용 엔드포인트 (뉴스 댓글 작성) ─────────────────
@router.post("/news/{news_id}/comments", response_model=schemas.CommentResponse, summary="뉴스 댓글 작성 (프론트 연동)")
def create_news_comment_compat(
    news_id: int,
    comment_data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    news = db.query(models.News).filter(models.News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다.")

    new_comment = models.Comment(
        content=comment_data.content,
        news_id=news_id,
        user_id=current_user.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


# ── 2. 수아님 프론트 주소 대응용 엔드포인트 (뉴스 댓글 조회) ─────────────────
@router.get("/news/{news_id}/comments", response_model=List[schemas.CommentResponse], summary="뉴스 댓글 조회 (프론트 연동)")
def get_news_comments_compat(
    news_id: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Comment)
        .filter(models.Comment.news_id == news_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )


# ── 3. 표준 공용 댓글 작성 (종목 토크방 등 확장용) ──────────────────────────
@router.post("/comments", response_model=schemas.CommentResponse, summary="공용 댓글 작성")
def create_comment(
    comment_data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_comment = models.Comment(
        content=comment_data.content,
        post_id=comment_data.post_id,
        news_id=comment_data.news_id,
        stock_symbol=comment_data.stock_symbol,
        user_id=current_user.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


# ── 4. 종목 토크방 댓글 조회 ──────────────────────────────────────────────────
@router.get("/comments/stock/{stock_symbol}", response_model=List[schemas.CommentResponse], summary="종목별 댓글 조회")
def get_comments_by_stock(
    stock_symbol: str,
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Comment)
        .filter(models.Comment.stock_symbol == stock_symbol)
        .order_by(models.Comment.created_at.desc())
        .all()
    )


# ── 5. 댓글 수정 ──────────────────────────────────────────────────────────────
@router.put("/comments/{comment_id}", response_model=schemas.CommentResponse, summary="댓글 수정")
def update_comment(
    comment_id: int,
    comment_data: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
        
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 수정할 수 있습니다.")
        
    comment.content = comment_data.content
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment


# ── 6. 댓글 삭제 ──────────────────────────────────────────────────────────────
@router.delete("/comments/{comment_id}", summary="댓글 삭제")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
        
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 삭제할 수 있습니다.")
        
    db.delete(comment)
    db.commit()
    return {"status": "success", "message": "댓글이 안전하게 삭제되었습니다."}