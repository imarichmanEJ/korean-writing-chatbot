from langgraph.graph import MessagesState
from typing import Literal, Optional
from typing_extensions import TypedDict 
from enum import Enum

#state
class Task(str, Enum):
    GENERATION = "generation"
    EVALUATION = "evaluation"
    SUMMARIZATION = "summarization"
    QA = "qa"
    ERROR = "error"

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


class WritingState(MessagesState):

    session_id : str
    task : Optional[Task] = None
    comment : str | None
    
    #문제
    question_type : Optional[QuestionType] = None
    question: str | None
    blank_type : Optional[BlankType] = None
    blank_data: Optional[BlankData] = None
    
    #답안
    user_answer : str | None
    user_essay_answer : str | None
    user_blank1_answer : str | None
    user_blank2_answer : str | None
    
    #채점
    total_score : float | None
    con_score: float | None
    org_score : float | None
    exp_score : float | None
    feedback : str | None

    #요약
    summary : str | None

    #이전데이터
    pre_feedback : str | None

    
class SupervisorTask(TypedDict):
    task : Optional[Task] = None
    question_type : Optional[QuestionType] = None
    blank_type : Optional[BlankType] = None
    comment : Optional[str]=None

class GenerationTask(TypedDict):
    question: str | None
    blank_type : Optional[BlankType] = None
    blank_data: Optional[BlankData] = None

class EvaluationArgTask(TypedDict):
    overall : str
    con : str
    org : str
    exp : str

class EvaluationBlankTask(TypedDict):
    blank_1_score: Literal[1, 3, 5]
    blank_1_feedback: str
    blank_2_score: Literal[1, 3, 5]
    blank_2_feedback: str
