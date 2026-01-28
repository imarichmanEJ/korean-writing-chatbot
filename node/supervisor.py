from core.prompt import supervisor_agent_prompt
from core.llm import get_supervisor_model
from node.state import WritingState, SupervisorTask, Task

from langgraph.graph import END
from langchain_core.messages import SystemMessage
import logging
import time

logger = logging.getLogger(__name__)
supervisor_model = get_supervisor_model()

def supervisor_node(state:WritingState):
    print("supervisor_agent 호출")

    try:

        user_message = state["messages"][-1].content
        task = state.get("task")
        question_type = state.get("question_type")
        blank_type = state.get("blank_type")
        
        if task == Task.EVALUATION:
            return state
        
        prompt = supervisor_agent_prompt.format(
            message=user_message, 
            question=state.get("question") or "(none)", 
            answer=state.get("user_answer") or "(none)"
        )

        try:
            structured_llm = supervisor_model.with_structured_output(SupervisorTask, include_raw=True)

            llm_start_time = time.time()
            response_container = structured_llm.invoke(
                [SystemMessage(content=prompt)]
            )
            llm_duration = (time.time() - llm_start_time) * 1000

            response = response_container['parsed']  #SupervisorTask 객체
            raw_message = response_container['raw']  #response_metadata가 담긴 AIMessage 객체

            # 토큰 정보 추출
            usage = raw_message.response_metadata.get('token_usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)

            # GPT-4o 비용 계산
            cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)

            #로깅
            logger.info(
                f"agent=supervisor_node "
                f"llm_duration={llm_duration:.2f}ms "
                f"prompt_tokens={prompt_tokens} "
                f"completion_tokens={completion_tokens} "
                f"total_tokens={total_tokens} "
                f"cost=${cost:.6f} "
                f"status=success"
            )

        except Exception as llm_error:
            logger.error(f"Supervisor LLM 호출 실패: {llm_error}")
            return {
                **state,
                "task": Task.QA,
                "comment": f"Supervisor LLM 호출 실패: {str(llm_error)}"
            }
        
        return {
            **state,
            "task": response.get("task"),
            "question_type": response.get("question_type") or question_type,
            "blank_type": response.get("blank_type") or blank_type,
            "comment": response.get("comment")
        }
        
    except Exception as e:
        logger.error(f"supervisor_agent 실행 중 에러: {e}")
        return {
            **state,
            "task": Task.QA,
            "comment": f"시스템 오류 발생: {str(e)}"
        }
    

def route_supervisor(state:WritingState):

    task = state.get("task")
    route_map = {
        'generation': 'generation',
        'evaluation': 'evaluation',
        'summarization': 'summarization',
        'qa': 'qa'
    }
    
    if task not in route_map:
        logger.warning(f"유효하지 않은 task: {task}, qa로 폴백")
        return 'qa'
    
    route = route_map[task]
    logger.info(f"Routing to: {route}")
    return route