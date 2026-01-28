"""
Question 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional
from typing_extensions import TypedDict 
from enum import Enum
from datetime import datetime, timezone


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(str, Enum):
    ARG = "ArgumentativeWriting"
    EXP = "ExpositoryWriting"
    BLANK = "Fill-in-the-Blank"

class BlankType(str, Enum):
    EMAIL = "EMAIL"
    USERPOST = "USER-POST"
    TEXTMESSAGES = "TEXT-MESSAGES"
    SHORTPASSAGE = "SHORT-PASSAGE"

class BlankData(TypedDict, total=False):
    blank_body: Optional[str]
    blank_stakeholder: Optional[str]
    blank_subject: Optional[str]
    blank_p1: Optional[str]
    blank_p2: Optional[str]

class Question(BaseModel):
    question_id: str = Field(..., description="문제 고유 ID")
    session_id : str = Field(..., description="세션 ID")
    question_type: QuestionType = Field(..., description="문제 유형")
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM, description="문제 난이도")
    question: str = Field(None, description="문제")
    blank_type : Optional[BlankType] = Field(None, description="빈칸채우기 문제 유형")
    blank_data: Optional[BlankData] = Field(None, description="빈칸채우기 문제 내용")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = Field(default=1, description="버전")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QuestionCreate(BaseModel):
    """문제 생성 요청용"""
    session_id : str
    question_type: QuestionType
    difficulty: Difficulty = Difficulty.MEDIUM
    question: str
    blank_type: Optional[BlankType] = None
    blank_data: Optional[BlankData] = None
    