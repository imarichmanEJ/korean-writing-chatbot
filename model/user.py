"""
User 데이터 모델
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """사용자 역할"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """사용자 데이터 모델"""
    user_id: str = Field(..., description="사용자 고유 ID")
    email: str = Field(..., description="이메일")
    username: str = Field(..., description="사용자 이름")
    role: UserRole = Field(default=UserRole.USER, description="역할")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(default=None, description="마지막 로그인")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """사용자 생성 요청용"""
    username: str
    email: str
    role: Optional[UserRole] = UserRole.USER


class UserUpdate(BaseModel):
    """사용자 수정 요청용"""