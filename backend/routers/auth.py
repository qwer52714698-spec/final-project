from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import SessionLocal
import models, auth_utils, schemas

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. 회원가입 (규격화된 데이터 사용)
@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 확인
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    # 사용자 이름 중복 확인
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")
    
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=auth_utils.get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. 로그인 (토큰 + 유저 정보 반환)
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm은 기본적으로 'username' 필드를 사용합니다.
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 생성 (유저네임을 sub로 저장)
    access_token = auth_utils.create_access_token(data={"sub": user.username})
    
    # 규격에 맞춰 토큰과 유저 정보를 함께 반환
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }