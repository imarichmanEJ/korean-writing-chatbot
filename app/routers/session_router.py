from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from repository.session_repository import SessionRepository
from repository.message_repository import MessageRepository


router = APIRouter(prefix="/sessions", tags=["sessions"])

#repository 인스턴스 생성
session_repo = SessionRepository()
message_repo = MessageRepository()

#<목록>
#GET / user/{user_id} : 사용자 세션 목록 조회
#GET / {session_id}/messages : 특정 세션 메세지 조회
#PUT / {session_id} : 특정 세션 제목 업데이트
#PATCH /{session_id} : 특정 세션 status 'deleted'로 변경


#GET / user/{user_id} : 사용자 세션 목록 조회
@router.get("/user/{user_id}")
async def get_user_sessions(user_id: str)-> Dict[str, Any]:
    """사용자의 세션 목록 조회(최대 10개)"""
    try:
        sessions = session_repo.get_user_sessions(user_id)
        
        return {
            "success": True,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "user_id": s.user_id,
                    "title": s.title,
                    "updated_at": s.updated_at.isoformat(),
                    "message_count": s.message_count,
                }
                for s in sessions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"세션 조회 실패: {str(e)}")
    

#GET / {session_id}/messages : 특정 세션 메세지 조회
@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, user_id: str):
    """특정 세션의 메시지 목록 조회"""
    try:
        session = session_repo.get_session_by_id(session_id, user_id)

        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        messages = message_repo.get_session_messages(session_id)
        
        return {
            "success": True,
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"✗ 메시지 조회 에러: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"메시지 조회 실패: {str(e)}")
    

#PUT / {session_id} : 특정 세션 제목 업데이트
class SessionTitleUpdate(BaseModel):
    title : str
    user_id : str

@router.put("/{session_id}")
async def update_session_title(session_id: str, request: SessionTitleUpdate):
    """세션 제목 수정"""
    try:
        
        user_id = request.user_id
        new_title = request.title
        
        if not new_title:
            raise HTTPException(status_code=400, detail="제목을 입력하세요")
                
        success = session_repo.update_session_title(session_id, user_id, new_title)            
        
        if success :
            return {
                "success": True,
                "message": "제목이 변경되었습니다"
            }
        else:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 권한이 없습니다")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="제목 변경 실패")

#PATCH /{session_id} : 특정 세션 status 'deleted'로 변경
@router.patch("/{session_id}")
async def delete_session(session_id: str, user_id : str):
    """세션 삭제"""
    try:

        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 정보가 없습니다")
        
        session = session_repo.get_session_by_id(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        if session.status == "DELETED":
            raise HTTPException(status_code=400, detail="이미 삭제된 세션입니다")
        
        session_repo.delete_session(session_id, user_id)
        
        return {"success": True, "message": "세션이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="세션 삭제 실패")

