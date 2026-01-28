from typing import Dict, Any, Optional
from datetime import datetime
import logging
from workflow.graph_builder import graph
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class LangGraphClient:
    """
    LangGraph 멀티에이전트 시스템과 통신하는 클라이언트
    """
    
    def __init__(self):

        self.graph = graph


    async def invoke(
        self, 
        session_id: str,
        user_id: str,
        user_message: str,
        context : Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        LangGraph 호출 및 응답 처리
        """

        try:
            logger.info(f"[{session_id}] LangGraph 호출 시작: {user_message[:50]}")
            
            state = self._prepare_state(session_id, user_message, context)
            
            config = {"configurable": {"thread_id": session_id}}
            result = await self.graph.ainvoke(state, config=config)
            
            parsed = self._parse_response(result)
            
            return parsed
            
        except Exception as e:
            logger.error(f"[{session_id}] LangGraph 호출 실패: {e}", exc_info=True)
            return {
                "task": "error",
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요."
            }
    
    
    def _prepare_state(self, session_id: str, user_message: str, context: Optional[dict]) -> Dict[str, Any]:
        """
        WritingState 형식으로 입력 준비
        """

        if context is None:
            context = {}

        task = context.get("task")
        question = context.get("question")
        question_type = context.get("question_type")
        user_answer = context.get("user_answer")
        pre_feedback = context.get("pre_feedback")

        state = {
            "session_id" : session_id,
            "messages": [HumanMessage(content=user_message)],
            "task" : task,
            "question" : question,
            "question_type" : question_type,
            "user_answer" : user_answer
        }

        return state
    
    
    def _parse_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Graph 응답을 Service가 사용하기 쉬운 형태로 변환
        """

        ai_response = result["messages"][-1].content
        task = result.get("task")

        parsed = {
            "response": ai_response,
            "task": task
        }

        if task == "generation":
            parsed.update({
                "question": result.get("question", ""),
                "question_type": result.get("question_type")
            })
            
            blank_data = result.get("blank_data")
            # blank_data가 있을 때만 추가
            if blank_data:
                parsed.update({
                    "blank_type" : result.get("blank_type"),
                    "blank_data": {
                        "blank_body": blank_data['blank_body'],
                        "blank_stakeholder": blank_data['blank_stakeholder'],
                        "blank_subject": blank_data['blank_subject'],
                        "blank_p1": blank_data['blank_p1'],
                        "blank_p2": blank_data['blank_p2']
                    }
                })
        
        elif task == "evaluation":
            parsed.update({
                "feedback": result.get("feedback", ""),
                "total_score": result.get("total_score", 0.0),
                "con_score": result.get("con_score"),
                "org_score": result.get("org_score"),
                "exp_score": result.get("exp_score")
            })
        
        elif task == "summarization":
            parsed["summary"] = result.get("summary")


        return parsed
