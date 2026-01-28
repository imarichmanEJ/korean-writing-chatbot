from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

class SessionStatus(str, Enum):
    """세션 상태"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Session(BaseModel):
    """세션 데이터 모델 """
    session_id: str = Field(..., description="세션 고유 ID (UUID)")
    user_id: str = Field(..., description="사용자 ID")
    title: str = Field(default="새 대화", description="세션 제목")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = Field(default=0, description="총 메시지 개수")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SessionCreate(BaseModel):
    """세션 생성 요청용"""
    user_id: str
    title: str = "새 대화"

class SessionUpdate(BaseModel):
    """세션 수정 요청용"""