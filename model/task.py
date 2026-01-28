from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class TaskType(str, Enum):
    """작업 유형"""
    GENERATION = "generation"
    EVALUATION = "evaluation"
    SUMMARIZATION = "summarization"
    QA = "qa"


class Task(BaseModel):
    """작업 데이터 모델 (학습 루틴 분석용)"""
    task_id: str = Field(..., description="작업 고유 ID (UUID)")
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    task_type: TaskType = Field(..., description="작업 유형")
    success: bool = Field(..., description="작업 성공 여부")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskCreate(BaseModel):
    """작업 생성 요청용"""
    session_id: str
    user_id: str
    task_type: TaskType
    success : bool