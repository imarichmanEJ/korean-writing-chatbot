from fastapi import APIRouter, HTTPException, Request
from services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()

# POST /chat : 채팅 엔드포인트
@router.post("")
async def chat(request: Request):

    try:
        data = await request.json()
    except Exception:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            raise HTTPException(status_code=400, detail="잘못된 요청 형식입니다")

    user_id = data.get("user_id")
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    submission_id = data.get("submission_id")
    evaluation_id = data.get("evaluation_id")
    
    user_message = data.get("user_message")
    answer = data.get("answer")
    
    try:
        
        result = await chat_service.process_chat(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            submission_id=submission_id,
            evaluation_id=evaluation_id,
            user_message=user_message,
            answer=answer
        )
        
        result = {
            "reply": result.get("reply"),
            "task" : result.get("task"),
            "session_id": result.get("session_id"),
            "question_id" : result.get("question_id"),
            "question_type" : result.get("question_type"),
            "question" : result.get("question"),
            "blank_type" : result.get("blank_type"),
            "blank_data" : result.get("blank_data"),
            "submission_id" : result.get("submission_id"),
            "evaluation_id" : result.get("evaluation_id")
        }
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )