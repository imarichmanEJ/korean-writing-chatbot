import jwt
from fastapi import APIRouter, HTTPException, Header
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from core.config import SECRET_KEY
from model.user import UserCreate, UserRole
from repository.user_repository import UserRepository


router = APIRouter(prefix="/auth", tags=["auth"])

#repository 인스턴스 생성
user_repo = UserRepository()


#<목록>
#POST /login : 사용자 로그인·회원가입
#GET /check : 사용자 계정 확인


# 설정
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 5

#POST /login : 사용자 로그인·회원가입
class LoginRequest(BaseModel):
    username: str

@router.post("/login")
async def login(data: LoginRequest):

    """테스트단계 : 간단한 로그인"""
    try:
        username = data.username.strip()
        
        if not username:
            return {"success": False, "message": "이름을 입력해주세요."}
        
        # 이메일 자동 생성 (임시)
        email = f"{username}@temp.local"
        
        # 기존 사용자 확인
        existing_user = user_repo.get_user_by_email(email)
        
        if existing_user:
            # 로그인 시간 업데이트
            user_repo.update_last_login(existing_user.user_id)
            user_id = existing_user.user_id
            user_username = existing_user.username
            message = f"환영합니다, {existing_user.username}님!"

        else:
            # 새 사용자 생성
            new_user = user_repo.create_user(
                UserCreate(
                    email=email,
                    username=username,
                    role=UserRole.USER
                )
            )
            user_id = new_user.user_id
            user_username = new_user.username
            message = f"가입되었습니다. 환영합니다, {new_user.username}님!"

        # JWT 토큰 생성
        payload = {
            "user_id": user_id,
            "username": user_username,
            "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "success": True,
            "token": token,
            "user_id": user_id,
            "username": user_username,
            "message": message
        }
    
    except Exception as e:
        import traceback
        print(f"✗ 로그인 에러: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "message": "로그인 중 오류가 발생했습니다."
        }


############################## MAIN-PAGE + LOGIN CHECK ##############################
#GET /check : 사용자 계정 확인
@router.get("/check")
async def check_auth(authorization: Optional[str] = Header(None)):
    """JWT 토큰 검증"""

    if not authorization:
        raise HTTPException(status_code=401, detail="No token")
    
    try:
        token = authorization.replace("Bearer ", "")
        
        # JWT 토큰 검증
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # 만료 시간 체크
        exp = payload.get("exp")
        if exp and datetime.now() > datetime.fromtimestamp(exp):
            raise HTTPException(status_code=401, detail="Token expired")
        
        user_id = payload.get("user_id")
        
        # DB에서 사용자 확인 (선택)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "authenticated": True,
            "user_id": user_id
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"✗ Auth check 에러: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

