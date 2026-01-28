from core.prompt import (
    evaluation_arg_prompt, 
    evaluation_arg_feedback_prompt,
    evaluation_blank_prompt
)
from core.config import FT_EVAL_MODEL_ID
from core.llm import get_evaluation_model, get_client
from node.state import (
    WritingState, 
    QuestionType, 
    BlankType, 
    EvaluationArgTask, 
    EvaluationBlankTask,
    Task
)
from langchain_core.messages import SystemMessage, AIMessage

import re
import logging
import time

logger = logging.getLogger(__name__)
evaluation_model = get_evaluation_model()
client = get_client()


def evaluation_node(state: WritingState):
    print("evaluation_node 호출")
    
    try:

        question_type = state.get("question_type")
        question = state.get("question")
        user_answer = state.get("user_answer")

        if question_type == QuestionType.ARG:

            evaluation = evaluate_argumentative(question_type, question, user_answer)

            return {
                **state,
                "messages" : [AIMessage(content=evaluation["feedback"])],
                "feedback": evaluation["feedback"],
                "total_score": evaluation["total_score"],
                "con_score": evaluation["con_score"],
                "org_score": evaluation["org_score"],
                "exp_score": evaluation["exp_score"]
            }
    
        elif question_type == QuestionType.BLANK:
            blank_type = state.get("blank_type")

            pattern = r'\(ㄱ\):\s*(.+)\n\(ㄴ\):\s*(.+)'
            match = re.search(pattern, user_answer)
            if match:
                user_blank1 = match.group(1).strip()
                user_blank2 = match.group(2).strip()

            evaluation = evaluate_fill_blank(question, blank_type, user_blank1, user_blank2)

            return {**state,
                    "messages" : [AIMessage(content=evaluation["feedback"])],
                    "feedback" : evaluation["feedback"],
                    "total_score" : evaluation["total_score"]
            }
        
        else:
            logger.warning(f"처리되지 않은 question_type: {question_type}")
            error_msg = "I apologize, but the question type for evaluation is not supported. Please submit your answer for an argumentative essay or fill-in-the-blank question."
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
                        
    except Exception as e:
        logger.error(f"evaluation_node 실행 중 에러: {e}", exc_info=True)
        error_msg = "I apologize, but an error occurred while evaluating your answer. Please try submitting again or let me know if you need help."
        return {
            **state,
            "messages" : [AIMessage(content=error_msg)],
            "task": Task.ERROR
        }



# Argumentative 평가
def evaluate_argumentative(question_type: str, question: str, answer: str) -> dict:
    """
    Argumentative 평가
    """
    try:
        
        # Fine-tuned 모델로 점수 채점
        eval_message = f'Korean writing Question: {question}\n\n\nResponse: {answer}'
        
        llm_start_time = time.time()
        completion = client.chat.completions.create(
            model=FT_EVAL_MODEL_ID,
            messages=[
                {"role": "system", "content": evaluation_arg_prompt},
                {"role": "user", "content": eval_message}
            ]
        )
        llm_duration = (time.time() - llm_start_time) * 1000

        # OpenAI 직접 호출 시 토큰 정보
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        total_tokens = completion.usage.total_tokens

        cost = (prompt_tokens * 0.0003 / 1000) + (completion_tokens * 0.0012 / 1000)

        logger.info(
            f"agent=evaluation_node_finetuned "
            f"llm_duration={llm_duration:.2f}ms "
            f"prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens} "
            f"total_tokens={total_tokens} "
            f"cost=${cost:.4f} "
            f"status=success"
        )

        scores_text = completion.choices[0].message.content
        
        # 점수 파싱 ( 전부 5점 변환)
        scores = parse_scores(scores_text)
        
        # 피드백 생성
        feedback_dict  = generate_arg_feedback(question_type, question, answer, scores)
        
        # 포맷팅
        formatted_feedback = format_argumentative_feedback(scores, feedback_dict)
        
        return {
            "feedback": formatted_feedback,
            "total_score": scores["total_score"],
            "con_score": scores["con_score"],
            "org_score": scores["org_score"],
            "exp_score": scores["exp_score"]
        }
    
    except Exception as e:
        logger.error(f"Argumentative/Expository 평가 실패: {e}", exc_info=True)
        return {
            "feedback": "An error occurred during the evaluation process.",
            "total_score": 0,
            "con_score": 0,
            "org_score": 0,
            "exp_score": 0
        }

def parse_scores(scores_text: str) -> dict:

    try:
        total_match = re.search(r'\[?total_score\]?\s*[:=]\s*(\d+|\[\d+\])', scores_text, re.IGNORECASE)
        con_match = re.search(r'\[?con_score\]?\s*[:=]\s*(\d+|\[\d+\])', scores_text, re.IGNORECASE)
        org_match = re.search(r'\[?org_score\]?\s*[:=]\s*(\d+|\[\d+\])', scores_text, re.IGNORECASE)
        exp_match = re.search(r'\[?exp_score\]?\s*[:=]\s*(\d+|\[\d+\])', scores_text, re.IGNORECASE)
        
        if not all([total_match, con_match, org_match, exp_match]):
            raise ValueError(f"점수 파싱 실패: {scores_text[:200]}")

        total_score_raw = int(total_match.group(1).strip('[]'))
        con_score_raw = int(con_match.group(1).strip('[]'))
        org_score_raw = int(org_match.group(1).strip('[]'))
        exp_score_raw = int(exp_match.group(1).strip('[]'))

        level = grade_level(total_score_raw)
        total_score = round(total_score_raw / 6, 0)
        con_score = round(con_score_raw / 3, 0)
        org_score = round(org_score_raw, 0)
        exp_score = round(exp_score_raw / 2, 0)
        
        scores = {
            'level': level,
            'total_score': int(total_score),
            'con_score': int(con_score),
            'org_score': int(org_score),
            'exp_score': int(exp_score)
        }
        
        logger.info(f"점수 파싱 완료: {scores}")
        return scores
        
    except Exception as e:
        logger.error(f"점수 파싱 실패: {e}, 원문: {scores_text[:200]}")
        return {
            'level': 'Level1',
            'total_score': 0,
            'con_score': 0,
            'org_score': 0,
            'exp_score': 0
        }
    

def grade_level(total_score):

    if total_score>=28:
        level = "Level6"
    elif total_score>=23:
        level = "Level5"
    elif total_score>=18:
        level = "Level4"
    elif total_score>=13:
        level = "Level3"
    elif total_score>=8:
        level = "Level2"
    else:
        level="Level1"
    return level


def generate_arg_feedback(question_type : QuestionType, question: str, user_answer: str, scores: dict) -> dict:
    
    total = scores.get('total_score',0)
    con = scores.get('con_score',0)
    org = scores.get('org_score',0)
    exp = scores.get('exp_score',0)

    prompt = evaluation_arg_feedback_prompt.format(
        question = question,
        user_answer = user_answer,
        total_score = total,
        con_score = con,
        org_score = org,
        exp_score = exp
    )
    
    try:
        structured_llm = evaluation_model.with_structured_output(EvaluationArgTask, include_raw=True)

        llm_start_time = time.time()
        response_container = structured_llm.invoke([SystemMessage(content=prompt)])
        llm_duration = (time.time() - llm_start_time) * 1000

        response = response_container['parsed']  #EvaluationArgTask 객체
        raw_message = response_container['raw']  #response_metadata가 담긴 AIMessage 객체

        # 토큰 정보 추출
        usage = raw_message.response_metadata.get('token_usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)

        # GPT-4o 비용 계산
        cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)

        # 로깅
        logger.info(
            f"agent=evaluation_node "
            f"llm_duration={llm_duration:.2f}ms "
            f"prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens} "
            f"total_tokens={total_tokens} "
            f"cost=${cost:.6f} "
            f"status=success"
        )

        return response
    
    except Exception as e:
        logger.error(f"피드백 생성 실패: {e}")
        return {
            "overall" : "An error occurred during the evaluation process.",
            "con" : "error",
            "org" : "error",
            "exp" : "error"
        }


def format_argumentative_feedback(scores: dict, feedback: dict) -> str:
    """점수 + 피드백 포맷팅"""
    result = f"""
## 📝 Evaluation of your Response to Argumentative writing Question

### Scores
- Total: {scores.get('total_score', 0)}/5
- Content: {scores.get('con_score', 0)}/5
- Organization: {scores.get('org_score', 0)}/5
- Expression: {scores.get('exp_score', 0)}/5

### Overall Feedback
{feedback.get('overall', '')}


### Detailed Feedback

**Content**
{feedback.get('con', '')}

**Organization**
{feedback.get('org', '')}

**Expression**
{feedback.get('exp', '')}
"""
    return result.strip()



# Fill-in-the-Blank 평가
def evaluate_fill_blank(question: str, blank_type: BlankType, user_blank1 : str, user_blank2 : str) -> dict:
    """
    Fill-in-the-Blank 평가
    """
    try:
        prompt = evaluation_blank_prompt.format(
            blank_type=blank_type,
            question=question,
            user_blank1 = user_blank1,
            user_blank2 = user_blank2
        )

        structured_llm = evaluation_model.with_structured_output(EvaluationArgTask, include_raw=True)
        
        llm_start_time = time.time()
        response_container = structured_llm.invoke([SystemMessage(content=prompt)])
        llm_duration = (time.time() - llm_start_time) * 1000

        response = response_container['parsed']  #EvaluationArgTask 객체
        raw_message = response_container['raw']  #response_metadata가 담긴 AIMessage 객체

        # 토큰 정보 추출
        usage = raw_message.response_metadata.get('token_usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)

        # GPT-4o 비용 계산
        cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)

        # 로깅
        logger.info(
            f"agent=evaluation_node "
            f"llm_duration={llm_duration:.2f}ms "
            f"prompt_tokens={prompt_tokens} "
            f"completion_tokens={completion_tokens} "
            f"total_tokens={total_tokens} "
            f"cost=${cost:.6f} "
            f"status=success"
        )

        total_score = response["blank_1_score"] + response["blank_2_score"]
        formatted_feedback = format_fill_blank_feedback(total_score, response)

        return {
            "total_score" : total_score, 
            "feedback" : formatted_feedback
        }
    
    except Exception as e:
        logger.error(f"Fill-in-the-Blank 평가 실패: {e}", exc_info=True)
        return {
            "total_score": 0,
            "feedback": "An error occurred during the evaluation process."
        }


def format_fill_blank_feedback(total_score: int, feedback: dict) -> str:
    """점수 + 피드백 포맷팅"""
    result = f"""
## 📝 Evaluation of your Response to Fill-in-the-Blank Question

### Total Score
{total_score}/10

### (ㄱ) evaluation
 - score : {feedback.get('blank_1_score')}/5
 - feedback : {feedback.get('blank_1_feedback')}

### (ㄴ) evaluation
 - score : {feedback.get('blank_2_score')}/5
 - feedback : {feedback.get('blank_2_feedback')}
"""
    return result.strip()
