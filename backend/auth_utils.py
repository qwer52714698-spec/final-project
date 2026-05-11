from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# 보안 설정 (나중에 .env로 옮기는 게 좋습니다)
SECRET_KEY = "your-very-secret-key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1일 동안 유효

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 비밀번호 암호화
def get_password_hash(password):
    return pwd_context.hash(password)

# 비밀번호 확인
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT 토큰 생성
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)