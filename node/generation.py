from core.prompt import (
    generation_arg_prompt,
    generation_blank_email_prompt,
    generation_blank_user_post_prompt,
    generation_blank_text_messages_prompt,
    generation_blank_short_passage_prompt
)
from core.llm import get_generation_model
from node.state import (
    WritingState,
    GenerationTask,
    Task,
    QuestionType,
    BlankType,
    BlankData
)
from langchain_core.messages import SystemMessage, AIMessage
import logging
import time

logger = logging.getLogger(__name__)
generation_model = get_generation_model()


PROMPT_MAP = {
    QuestionType.ARG: generation_arg_prompt,
    (QuestionType.BLANK, BlankType.EMAIL): generation_blank_email_prompt,
    (QuestionType.BLANK, BlankType.USERPOST): generation_blank_user_post_prompt,
    (QuestionType.BLANK, BlankType.TEXTMESSAGES): generation_blank_text_messages_prompt,
    (QuestionType.BLANK, BlankType.SHORTPASSAGE): generation_blank_short_passage_prompt,
}

def get_generation_prompt(
        question_type: str, 
        blank_type: str | None, 
        user_message : str
) -> str:
    """question_type/blank_type에 따른 프롬프트 반환"""

    if question_type == QuestionType.ARG:
        prompt_template = PROMPT_MAP.get(question_type)
        return prompt_template.format(message = user_message) if prompt_template else None
    
    elif question_type == QuestionType.BLANK and blank_type:
        prompt_template = PROMPT_MAP.get((question_type, blank_type))
        return prompt_template.format(message = user_message) if prompt_template else None
    
    return None


def generation_node(state:WritingState):
    """문제 생성 노드"""
    print("generation_agent 호출")

    try:

        #입력값
        user_message = state['messages'][-1].content
        question_type = state['question_type']
        blank_type = state['blank_type']
        
        #프롬프트
        prompt = get_generation_prompt(question_type, blank_type, user_message)

        if not prompt:
            logger.error(f"유효하지 않은 question_type/blank_type: {question_type}/{blank_type}")
            error_msg = AIMessage(content=
                    "I apologize, but the question type you requested is not supported. Please ask me to generate an argumentative essay, expository essay, or fill-in-the-blank question."
                )
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }

        #LLM 호출
        try:
            structured_llm = generation_model.with_structured_output(GenerationTask, include_raw=True)

            llm_start_time = time.time()
            response_container = structured_llm.invoke(
                [SystemMessage(content=prompt)]
            )
            llm_duration = (time.time() - llm_start_time) * 1000

            response = response_container['parsed']  #GenerationTask 객체
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
                f"agent=generation_node "
                f"llm_duration={llm_duration:.2f}ms "
                f"prompt_tokens={prompt_tokens} "
                f"completion_tokens={completion_tokens} "
                f"total_tokens={total_tokens} "
                f"cost=${cost:.6f} "
                f"status=success"
            )


            if not response:
                raise ValueError("Empty response from LLM")
        
        except Exception as llm_error:
            logger.error(f"Generation LLM 호출 실패: {llm_error}", exc_info=True)
            error_msg = "I apologize, but I was unable to generate a question. Please try again or ask me to generate a different type of question."
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
        
        # 응답 처리
        if question_type == QuestionType.ARG:

            question = response.get("question")
            ai_message = f"""
Question generated!
Write your answer in the left panel and click Submit when you're done.
Feel free to ask me questions in the chat while you work!

{question}
"""
            return {
                **state,
                "messages" : [AIMessage(content=ai_message)],
                "question": question
            }
        
        elif question_type == QuestionType.BLANK:

            blank_type = response.get("blank_type")
            blank_data = response.get("blank_data", {})

            if blank_type in [BlankType.EMAIL, BlankType.USERPOST]:
                 question = (
                    f"blank_stakeholder: {blank_data['blank_stakeholder']}\n"
                    f"blank_subject: {blank_data['blank_subject']}\n"
                    f"blank_body:\n{blank_data['blank_body']}"
                )
            
            elif blank_type == BlankType.TEXTMESSAGES:
                question = (
                    f"blank_p1:\n{blank_data['blank_p1']}\n"
                    f"blank_p2:\n{blank_data['blank_p2']}"
                )
            
            elif blank_type == BlankType.SHORTPASSAGE:
                question = f"blank_body:\n{blank_data['blank_body']}"

            else:
                logger.error(f"알 수 없는 blank_type: {blank_type}")
                error_msg = "I apologize, but the blank type you requested is not supported. Please try generating a different type of fill-in-the-blank question."
                return {
                    **state,
                    "messages" : [AIMessage(content=error_msg)],
                    "task": Task.ERROR
                }
            
            ai_message = f"""
Question generated!
Write your answer in the left panel and click Submit when you're done.
Feel free to ask me questions in the chat while you work!

{question}
"""
            
            return {
                **state,
                "messages" : [AIMessage(content=ai_message)],
                "question" : question,
                "blank_type" : blank_type,
                "blank_data": BlankData(
                    blank_body=blank_data.get("blank_body"),
                    blank_stakeholder=blank_data.get("blank_stakeholder"),
                    blank_subject=blank_data.get("blank_subject"),
                    blank_p1=blank_data.get("blank_p1"),
                    blank_p2=blank_data.get("blank_p2")
                )
            }
        
        else:
            logger.warning(f"처리되지 않은 question_type: {question_type}")
            return state

    except Exception as e:
        logger.error(f"generation_agent 실행 중 에러: {e}", exc_info=True)
        error_msg = "I apologize, but an error occurred while generating your question. Please try again or let me know if you need help."
        return {
            **state,
            "messages" : [AIMessage(content=error_msg)],
            "task": Task.ERROR
        }




