"""
Submission 데이터 모델
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

class QuestionType(str, Enum):
    ARG = "ArgumentativeWriting"
    EXP = "ExpositoryWriting"
    BLANK = "Fill-in-the-Blank"

class BlankType(str, Enum):
    EMAIL = "EMAIL"
    USERPOST = "USER-POST"
    TEXTMESSAGES = "TEXT-MESSAGES"
    SHORTPASSAGE = "SHORT-PASSAGE"

class Submission(BaseModel):
    """답안 제출 데이터 모델"""
    submission_id: str = Field(..., description="제출 고유 ID")
    user_id: str = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    question_id: str = Field(..., description="문제 ID")
    question_type: QuestionType = Field(..., description="문제 유형")
    blank_type : Optional[BlankType] = Field(None, description="빈칸채우기 문제 유형")
    answer: str = Field(..., description="사용자 답안")
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SubmissionCreate(BaseModel):
    """답안 제출 생성 요청용"""
    user_id: str
    session_id: str
    question_id: str
    question_type: QuestionType
    blank_type: Optional[BlankType] = None
    answer: str
    