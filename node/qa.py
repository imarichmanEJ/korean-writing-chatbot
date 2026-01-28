
from core.prompt import qa_node_prompt
from core.llm import get_qa_model
from node.state import WritingState, Task
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.tools import WikipediaQueryRun
# from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import WikipediaAPIWrapper
import logging
import time

logger = logging.getLogger(__name__)


# 도구
wikipedia = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(),
        name="wikipedia",
        description="..."
)

# tavily_search = TavilySearchResults(
#     max_results=3,
#     name="tavily_search_results_json",
#     description="..."
# )
#tools = [wikipedia, tavily_search]

tools = [wikipedia]


def qa_node(state: WritingState):
    """질의응답"""
    print("qa_node 호출")
    
    try:

        qa_model = get_qa_model()
        qa_model_with_tools = qa_model.bind_tools(tools)
        
        conversation_history = format_conversation_history(state.get("messages", []))
        
        prompt = qa_node_prompt.format(
            conversation_history=conversation_history
        )
        
        messages = [SystemMessage(content=prompt)] + state.get("messages", [])

        try:
            
            llm_start_time = time.time()
            response = qa_model_with_tools.invoke(messages)
            llm_duration = (time.time() - llm_start_time) * 1000  # ms

            # 토큰 정보 추출
            usage = response.response_metadata.get('token_usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)

            # GPT-4o 비용 계산
            cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)

            # 로깅
            logger.info(
                f"agent=qa_node "
                f"llm_duration={llm_duration:.2f}ms "
                f"prompt_tokens={prompt_tokens} "
                f"completion_tokens={completion_tokens} "
                f"total_tokens={total_tokens} "
                f"cost=${cost:.6f} "
                f"status=success"
            )

            # Tool 호출 확인 ← 추가
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    print(f"Tool 호출됨: {tool_call.get('name', 'Unknown')}")

            else:
                print("Tool 호출 없음 (직접 답변)")
                
            return {
                **state,
                "messages": [response]
            }
        
        except Exception as llm_error:
            logger.error(f"QA LLM 호출 실패: {llm_error}", exc_info=True)
            fallback_response = create_fallback_response()
            return {
                **state,
                "messages" : [fallback_response],
                "task": Task.ERROR
            }
    
    except Exception as e:
        logger.error(f"qa_node 실행 중 에러: {e}", exc_info=True)
        error_response = AIMessage(content="I apologize for the inconvenience. Please try again later.")
        return {
            **state,
            "messages": [error_response],
            "task": Task.ERROR
        }


def format_conversation_history(messages: list) -> str:
    """
    대화 이력 중 불필요한 것 제외 및 긴 메시지 축약
    """
    if not messages:
        return "No conversation history."
    
    formatted = []
    
    # 최근 10개 메시지만 (너무 길면 프롬프트 비효율)
    recent_messages = messages[-10:]
    
    for i, msg in enumerate(recent_messages, 1):
        if isinstance(msg, HumanMessage):
            role = "User"
            content = msg.content
        elif isinstance(msg, AIMessage):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                continue
            role = "Assistant"
            content = msg.content
        elif isinstance(msg, SystemMessage):
            continue
        else:
            role = "System"
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
        
        if content and len(content) > 300:
            content = content[:300] + "... [truncated]"
        
        if content:  # 빈 content 제외
            formatted.append(f"[{i}] {role}: {content}")
    
    return "\n".join(formatted) if formatted else "No conversation history."


def create_fallback_response():
    """
    LLM 호출 실패 시 fallback 응답 생성
    """
    fallback_content = """I apologize, but I'm having trouble generating a response right now. 

Please try:
- Asking your question in a different way
- Breaking down complex questions into smaller parts
- Asking about specific topics like:
  • Korean writing techniques
  • Essay structure and organization
  • Grammar and expression tips
  • How to use this learning system

I'm here to help with your Korean writing practice!"""
    
    return AIMessage(content=fallback_content)