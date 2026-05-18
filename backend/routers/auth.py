from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from jose import jwt, JWTError
import models
import auth_utils
import schemas

router = APIRouter(prefix="/auth", tags=["인증"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="로그인 정보가 유효하지 않거나 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/signup", response_model=schemas.UserResponse)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
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


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.email == form_data.username) | 
        (models.User.username == form_data.username)
    ).first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_utils.create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }
