
from model.session import SessionCreate
from model.message import MessageCreate, MessageRole
from model.task import TaskCreate, TaskType
from model.question import QuestionCreate
from model.submission import SubmissionCreate
from model.evaluation import EvaluationCreate
from repository.session_repository import SessionRepository
from repository.message_repository import MessageRepository
from repository.task_repository import TaskRepository
from repository.question_repository import QuestionRepository
from repository.submission_repository import SubmissionRepository
from repository.evaluation_repository import EvaluationRepository
from clients.langgraph_client import LangGraphClient

from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


# class ChatService:
#     def __init__(self):
#         self.session_repo = SessionRepository()
#         self.message_repo = MessageRepository()
#         self.task_repo = TaskRepository()
#         self.question_repo = QuestionRepository()
#         self.submission_repo = SubmissionRepository()
#         self.evaluation_repo = EvaluationRepository()
#         self.graph_client = LangGraphClient()

class ChatService:
    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        message_repo: Optional[MessageRepository] = None,
        task_repo: Optional[TaskRepository] = None,
        question_repo: Optional[QuestionRepository] = None,
        submission_repo: Optional[SubmissionRepository] = None,
        evaluation_repo: Optional[EvaluationRepository] = None,
        graph_client: Optional[LangGraphClient] = None
    ):
        self.session_repo = session_repo or SessionRepository()
        self.message_repo = message_repo or MessageRepository()
        self.task_repo = task_repo or TaskRepository()
        self.question_repo = question_repo or QuestionRepository()
        self.submission_repo = submission_repo or SubmissionRepository()
        self.evaluation_repo = evaluation_repo or EvaluationRepository()
        self.graph_client = graph_client or LangGraphClient()

    async def process_chat(
        self,
        user_id: str,
        session_id: Optional[str],
        question_id: Optional[str],
        submission_id: Optional[str],
        evaluation_id: Optional[str],
        user_message: Optional[str],
        answer: Optional[str]
    ) -> Dict[str, Any]:
        """ 채팅 처리 메인 로직 """

        # ==================== 1. 세션 검증/생성 ====================
        session_id = await self._get_or_create_session(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message
        )
        
        # ==================== 2. Context 구성 ====================
        context = await self._build_context(
            session_id=session_id,
            question_id=question_id,
            answer=answer,
            submission_id=submission_id,
            evaluation_id=evaluation_id
        )

        # ==================== 3. LangGraph 실행 ====================
        try:
            result = await self.graph_client.invoke(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message or "답안을 제출합니다",
                context=context
            )
        except Exception as e:
            logger.error(f"LangGraph 실행 실패: {e}", exc_info=True)
            raise Exception("채팅 처리 중 오류가 발생했습니다")
        
        response_text = result.get("response", "")
        task = result.get("task", "qa")
        question_type = result.get("question_type")

        # ==================== 4. Task별 예외처리 ====================        

        # ==================== 5. DB 저장 ====================
        # 5.1 User message 저장
        message_to_save = answer if answer else user_message
        try:
            self.message_repo.create_message(
                MessageCreate(
                    session_id=session_id,
                    role=MessageRole.USER,
                    content=message_to_save
                )
            )
        except Exception as e:
            logger.error(f"User 메시지 저장 실패: {e}")
        

        # 5.2 Task별 데이터 저장
        new_question_id = None
        new_submission_id = None
        new_evaluation_id = None
        
        # Generation: Question 저장
        if task == "generation":
            new_question_id = await self._save_question(
                result=result,
                session_id=session_id
            )
        
        # Evaluation: Submission + Evaluation 저장
        elif task == "evaluation" and question_id:
            new_submission_id, new_evaluation_id = await self._save_evaluation(
                result=result,
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                answer=answer,
                response_text=response_text
            )
        
        # 5.3 Task 생성 및 저장
        task_obj = None
        try:
            task_obj = self.task_repo.create_task(
                TaskCreate(
                    session_id=session_id,
                    user_id=user_id,
                    task_type=task,
                    success=False
                )
            )
        except Exception as e:
            logger.error(f"Task 저장 실패: {e}")
        
        # 5.4 Assistant message 저장
        try:
            self.message_repo.create_message(
                MessageCreate(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=response_text
                )
            )
        except Exception as e:
            logger.error(f"Assistant 메시지 저장 실패: {e}")
        
        # 5.5 세션 업데이트
        try:
            # 메시지 카운트 +2 (user + assistant)
            self.session_repo.increment_message_count(session_id, user_id, increment=2)
            
            # Task 상태 업데이트
            if task_obj:
                self.task_repo.update_task_status(
                    task_id=task_obj.task_id,
                    success=True
                )

        except Exception as e:
            logger.error(f"세션/Task 업데이트 실패: {e}")
        
        # ==================== 6. Response 구성 ====================
        return self._build_response(
            task_cate=task,
            response_text=response_text,
            session_id=session_id,
            result=result,
            new_question_id=new_question_id,
            new_submission_id=new_submission_id,
            new_evaluation_id=new_evaluation_id,
            question_id=question_id,
            question_type=question_type
        )

    
    #세션 조회/생성
    async def _get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str],
        user_message: Optional[str]
    ) -> str:
        """
        세션 조회 또는 생성
        
        Args:
            user_id: 사용자 ID
            session_id: 세션 ID (없으면 None)
            user_message: 사용자 메시지 (없으면 None)
        
        Returns:
            session_id (기존 또는 새로 생성된)
        """
        # 세션 ID가 있으면 조회
        if session_id:
            session = self.session_repo.get_session_by_id(session_id, user_id)
            if session:
                logger.info(f"기존 세션 사용: {session_id}")
                return session_id
        
        # 세션 없으면 새로 생성
        title = self._generate_session_title(user_message)
        
        new_session = self.session_repo.create_session(
            SessionCreate(user_id=user_id, title=title)
        )
        
        logger.info(f"새 세션 생성: {new_session.session_id}")
        return new_session.session_id
    

    #세션 제목 생성
    def _generate_session_title(self, user_message: Optional[str]) -> str:
        """
        세션 제목 생성
        """
        if not user_message:
            return "새 대화"
        
        if len(user_message) > 20:
            return user_message[:20] + "..."
        
        return user_message

    #LangGraph에 넘길 context 구성
    async def _build_context(
        self,
        session_id: str,
        question_id: Optional[str],
        answer: Optional[str],
        submission_id: Optional[str],
        evaluation_id: Optional[str]        
    ) -> Dict[str, Any]:
        """
        LangGraph 실행을 위한 context 구성
        
        Args:
            session_id: 세션 ID
            question_id: 문제 ID
            answer: 답안
            submission_id: 제출 ID
            evaluation_id: 평가 ID        
        Returns:
            context 딕셔너리
        """
        context = {}
        
        # ==================== 답안 제출 시 ====================
        if answer:
            context["task"] = "evaluation"
            context["user_answer"] = answer
            
            # question 검증 및 데이터 추출
            if question_id:
                question = self.question_repo.get_question_by_id(question_id)
                
                if question and question.session_id == session_id:
                    context["question"] = question.question
                    context["question_type"] = question.question_type
                    if question.blank_data:
                        context["blank_type"] = question.blank_type
                        context["blank_data"] = question.blank_data

                    logger.info(f"Question 검증 완료: {question_id}")
                else:
                    logger.warning(f"Question 검증 실패: {question_id}")
        
        # ==================== 일반 메시지 시 ====================
        else:
            # question 검증
            if question_id:
                question = self.question_repo.get_question_by_id(question_id)
                
                if question and question.session_id == session_id:
                    context["question"] = question.question
                    context["question_type"] = question.question_type
                    if question.blank_data:
                        context["blank_type"] = question.blank_type
                        context["blank_data"] = question.blank_data
                    
                    logger.info(f"Question 검증 완료: {question_id}")
            
            # submission & evaluation 검증
            if submission_id and evaluation_id:

                evaluation = self.evaluation_repo.get_evaluation_by_id(evaluation_id)
                
                context["pre_feedback"] = evaluation.feedback
        
        return context
    
    #GENERATION : langgraph 출력값 Question 저장
    async def _save_question(
        self,
        result: Dict[str, Any],
        session_id: str
    ) -> Optional[str]:
        """Question 저장 (Generation 시)"""
        
        question = result.get("question")

        if not question:
            logger.warning("Generation 결과에 생성된 question이 없음")
            return None
        
        try:
            question_type = result.get("question_type")
            blank_type = None
            blank_data = None
            
            if question_type == "Fill-in-the-Blank":
                blank_type = result.get("blank_type")
                blank_data = result.get("blank_data")
            
            question_obj = self.question_repo.create_question(
                QuestionCreate(
                    session_id = session_id,
                    question_type = question_type,
                    difficulty = "medium",
                    question = question,
                    blank_type = blank_type,
                    blank_data = blank_data
                )
            )
            
            logger.info(f"Question 저장 완료: {question_obj.question_id}")
            return question_obj.question_id
        
        except Exception as e:
            logger.error(f"Question 저장 실패: {e}")
            return None

    async def _save_evaluation(
        self,
        result: Dict[str, Any],
        user_id: str,
        session_id: str,
        question_id: str,
        answer: str,
        response_text: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Submission + Evaluation 저장"""
        try:

            # Question 조회
            question = self.question_repo.get_question_by_id(question_id)
            if not question:
                logger.error(f"Question 찾을 수 없음: {question_id}")
                return None, None
            
            # Submission 저장
            submission_obj = self.submission_repo.create_submission(
                SubmissionCreate(
                    user_id=user_id,
                    session_id=session_id,
                    question_id=question_id,
                    question_type=question.question_type,
                    blank_type = question.blank_type,
                    answer=answer
                )
            )
            
            total_score = result.get("total_score", 0.0)
            con_score = result.get("con_score", 0.0)
            org_score = result.get("org_score", 0.0)
            exp_score = result.get("exp_score", 0.0)
            feedback = result.get("feedback")
            
            # Evaluation 저장
            evaluation_obj = self.evaluation_repo.create_evaluation(
                EvaluationCreate(
                    submission_id=submission_obj.submission_id,
                    user_id=user_id,
                    session_id=session_id,
                    question_id=question_id,
                    question_type=question.question_type,
                    total_score=total_score,
                    con_score = con_score,
                    org_score = org_score,
                    exp_score=exp_score,
                    feedback=feedback
                )
            )
            
            logger.info(f"Submission/Evaluation 저장 완료: {submission_obj.submission_id}")
            return submission_obj.submission_id, evaluation_obj.evaluation_id
        
        except Exception as e:
            logger.error(f"Submission/Evaluation 저장 실패: {e}")
            return None, None


    def _build_response(
        self,
        task_cate: str,
        response_text: str,
        session_id: str,
        result: Dict[str, Any],
        new_question_id: Optional[str],
        new_submission_id: Optional[str],
        new_evaluation_id: Optional[str],
        question_id: Optional[str],
        question_type: Optional[str]
    ) -> Dict[str, Any]:
        """Task별 응답 데이터 구성"""
        
        response_data = {
            "reply": response_text,
            "task": task_cate,
            "session_id": session_id
        }
        
        # Generation 응답
        if task_cate == "generation" and new_question_id:
            response_data["question"] = result.get("question")
            response_data["question_id"] = new_question_id
            response_data["question_type"] = question_type
            
            # Blank 데이터
            if question_type == "Fill-in-the-Blank":
                response_data["blank_type"] = result.get("blank_type")
                response_data["blank_data"] = result.get("blank_data")
        
        # Evaluation 응답
        elif task_cate == "evaluation" and new_submission_id:
            response_data["question_id"] = question_id
            response_data["submission_id"] = new_submission_id
            response_data["evaluation_id"] = new_evaluation_id
        
        return response_data
