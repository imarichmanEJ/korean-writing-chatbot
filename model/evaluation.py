"""
Evaluation 데이터 모델
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

class QuestionType(str, Enum):
    ARG = "ArgumentativeWriting"
    EXP = "ExpositoryWriting"
    BLANK = "Fill-in-the-Blank"

class Evaluation(BaseModel):
    """채점 결과 데이터 모델"""
    evaluation_id: str = Field(..., description="채점 고유 ID")
    submission_id: str = Field(..., description="제출 ID")
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    question_id: str = Field(..., description="문제 ID")
    question_type: QuestionType = Field(..., description="문제 유형")
    total_score : float = Field(..., description="점수 총점")
    con_score: Optional[float] = Field(None, description="con 점수")
    org_score : Optional[float] = Field(None, description="org 점수")
    exp_score : Optional[float] = Field(None, description="exp 점수")
    feedback: str = Field(..., description="피드백")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EvaluationCreate(BaseModel):
    """채점 생성 요청용"""
    submission_id: str
    user_id : str
    session_id: str
    question_id : str
    question_type: QuestionType
    total_score : float
    con_score: Optional[float] = None
    org_score : Optional[float] = None
    exp_score : Optional[float] = None
    feedback: str