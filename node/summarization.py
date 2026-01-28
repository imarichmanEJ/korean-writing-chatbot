from core.prompt import summarization_node_prompt
from core.llm import get_summarization_model
from node.state import WritingState, Task
from repository.evaluation_repository import EvaluationRepository
from langchain_core.messages import SystemMessage, AIMessage
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)
summarization_model = get_summarization_model()
evaluation_repo = EvaluationRepository()


def summarization_node(state:WritingState):
    print("summarization 호출")

    try:
        # 1. 세션 ID 추출
        session_id = state.get("session_id")
        
        if not session_id:
            logger.error("session_id가 없습니다")
            error_msg = "I apologize, but I couldn't find the session information. Please try again or start a new conversation."
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
        
        # 2. 이 세션의 평가 이력 조회
        try:
            evaluations = evaluation_repo.get_session_evaluations(session_id)
        except Exception as db_error:
            logger.error(f"[{session_id}] Evaluation 조회 실패: {db_error}", exc_info=True)
            error_msg = "I apologize, but I couldn't retrieve your evaluation history. Please try again later."
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
        
        # 3. 평가 이력 검증
        if not evaluations:
            logger.warning(f"[{session_id}] 요약할 평가 이력이 없습니다")
            error_msg = "You don't have any evaluation history yet in this session. Complete some writing questions first, and then I can provide you with a summary of your progress!"
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
        
        # 4. 세션 통계 계산
        stats = calculate_session_statistics(evaluations)
        
        # 5. 평가 이력 포맷팅
        evaluation_summary = format_evaluation_history(evaluations)
        
        # 6. 날짜 범위 계산
        start_date, end_date = calculate_date_range(evaluations)
        
        # 7. 프롬프트 구성
        prompt = summarization_node_prompt.format(
            session_id=session_id,
            evaluation_history=evaluation_summary,
            statistics=format_statistics(stats),
            start_date=start_date,
            end_date=end_date
        )

        # 8. LLM 호출
        try:
            llm_start_time = time.time()
            response = summarization_model.invoke([SystemMessage(content=prompt)])
            llm_duration = (time.time() - llm_start_time) * 1000

            # 토큰 정보 추출
            usage = response.response_metadata.get('token_usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)

            # GPT-4o 비용 계산
            cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)

            #로깅
            logger.info(
                f"agent=summarization_node "
                f"llm_duration={llm_duration:.2f}ms "
                f"prompt_tokens={prompt_tokens} "
                f"completion_tokens={completion_tokens} "
                f"total_tokens={total_tokens} "
                f"cost=${cost:.6f} "
                f"status=success"
            )
            
            summary = response.content
            
            return {
                **state,
                "messages" : [response],
                "summary": summary
            }
        
        except Exception as llm_error:
            logger.error(f"[{session_id}] LLM 호출 실패: {llm_error}", exc_info=True)
            error_msg = "I apologize, but an error occurred while generating your summary. Please try again or let me know if you need help."
            return {
                **state,
                "messages" : [AIMessage(content=error_msg)],
                "task": Task.ERROR
            }
    
    except Exception as e:
        logger.error(f"summarization_node 실행 중 에러: {e}", exc_info=True)
        error_msg = "I apologize, but an error occurred while summarizing your session. Please try again or contact support if the issue persists."
        return {
            **state,
            "messages" : [AIMessage(content=error_msg)],
            "task": Task.ERROR
        }
        

def calculate_session_statistics(evaluations: list) -> dict:
    """
    세션 통계 계산
    """
    if not evaluations:
        return {
            'total_count': 0,
            'by_question_type': {}
        }
    
    # 문제 유형별 분류
    by_type = {}
    
    for eval in evaluations:
        type_str = eval.question_type.value
        
        if type_str not in by_type:
            by_type[type_str] = {
                'count': 0,
                'scores': []
            }
        
        by_type[type_str]['count'] += 1
        by_type[type_str]['scores'].append(eval.total_score)

    # 통계 계산
    for type_str in by_type:
        scores = by_type[type_str]['scores']
        by_type[type_str]['average_score'] = round(sum(scores) / len(scores), 2)
        by_type[type_str]['highest_score'] = max(scores)
        by_type[type_str]['lowest_score'] = min(scores)
        del by_type[type_str]['scores']
    
    return {
        'total_count': len(evaluations),
        'by_question_type': by_type
    }
    
def format_statistics(stats: dict) -> str:
    """
    세션 통계 데이터 문자열로 포맷팅
    """
    lines = [
        "="*50,
        "SESSION STATISTICS",
        "="*50,
        f"Total Evaluations: {stats['total_count']}",
        ""
    ]
    
    for question_type, type_stats in stats['by_question_type'].items():
        lines.append(f"{question_type}:")
        lines.append(f"  - Questions Completed: {type_stats['count']}")
        lines.append(f"  - Average Score: {type_stats['average_score']:.2f}")
        lines.append(f"  - Highest Score: {type_stats['highest_score']:.2f}")
        lines.append(f"  - Lowest Score: {type_stats['lowest_score']:.2f}")
        lines.append("")
    
    return "\n".join(lines)


def format_evaluation_history(evaluations: list) -> str:
    """
    평가 이력 형태 변환
    """
    formatted = []
    
    for i, eval in enumerate(evaluations, 1):
        eval_info = [
            f"{'='*50}",
            f"Evaluation #{i}",
            f"Question Type: {eval.question_type.value}",
            f"Date: {eval.created_at.strftime('%Y-%m-%d %H:%M')}"
        ]
        
        # 점수 (문제 유형에 따라)
        if eval.question_type.value in ["ArgumentativeWriting", "ExpositoryWriting"]:
            eval_info.append(f"Total Score: {eval.total_score}/5")
            if eval.con_score is not None:
                eval_info.append(f"  - Content (CON): {eval.con_score}/5")
            if eval.org_score is not None:
                eval_info.append(f"  - Organization (ORG): {eval.org_score}/5")
            if eval.exp_score is not None:
                eval_info.append(f"  - Expression (EXP): {eval.exp_score}/5")
        else:  # Fill-in-the-Blank
            eval_info.append(f"Total Score: {eval.total_score}/10")
        
        # 피드백 전체
        if eval.feedback:
            eval_info.append("")
            eval_info.append("Feedback:")
            eval_info.append(eval.feedback)
        
        formatted.append("\n".join(eval_info))
    
    return "\n\n".join(formatted)


def calculate_date_range(evaluations: list) -> tuple[str, str]:
    """
    세션 날짜 범위
    """
    try:
        # 가장 오래된 평가일자
        oldest = evaluations[-1]
        start_date = oldest.created_at.strftime("%Y-%m-%d")
        
        # 가장 최근 평가일자
        newest = evaluations[0]
        end_date = newest.created_at.strftime("%Y-%m-%d")
        
        return start_date, end_date
    
    except Exception as e:
        logger.warning(f"날짜 계산 실패: {e}")
        today = datetime.now().strftime("%Y-%m-%d")
        return today, today
