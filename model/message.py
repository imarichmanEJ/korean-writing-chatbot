from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class MessageRole(str, Enum):
    """메시지 발신자 역할"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """메시지 데이터 모델"""
    message_id: str = Field(..., description="메시지 고유 ID (UUID)")
    session_id: str = Field(..., description="세션 ID")
    role: MessageRole = Field(..., description="발신자 역할")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="전송 시각")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageCreate(BaseModel):
    """메시지 생성 요청용"""
    session_id: str
    role: MessageRole
    content: str


class MessageResponse(BaseModel):
    """메시지 응답용 (API)"""
    message_id: str
    role: MessageRole
    content: str
    timestamp: datetime