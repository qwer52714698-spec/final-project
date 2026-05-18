from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader # 💡 더 유연한 검증을 위해 추가
from sqlalchemy.orm import Session
from database import SessionLocal
import models

SECRET_KEY = "your-very-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# 💡 OAuth2PasswordBearer 대신 더 직관적인 APIKeyHeader를 사용해 봅니다.
# 프론트에서 보내는 "Authorization" 헤더를 직접 읽습니다.
header_scheme = APIKeyHeader(name="Authorization")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(auth_header: str = Depends(header_scheme), db: Session = Depends(get_db)):
    # 💡 이제 터미널에 무조건 찍혀야 합니다.
    print(f"📡 헤더에서 읽은 값: {auth_header}")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 실패",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # "Bearer <token>" 형식에서 토큰만 추출
        if not auth_header.startswith("Bearer "):
            print("❌ 'Bearer ' 접두사가 없습니다.")
            raise credentials_exception
        
        token = auth_header.split(" ")[1]
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            raise credentials_exception
            
        print(f"🎉 인증 성공: {username}")
        return user
        
    except Exception as e:
        print(f"❌ 최종 에러 발생: {str(e)}")
        raise credentials_exception
