import boto3
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from model.session import Session, SessionCreate, SessionStatus
from core.config import settings
from boto3.dynamodb.conditions import Key
import time
import logging

logger = logging.getLogger(__name__)

class SessionRepository:
    def __init__(self):
        """DynamoDB 연결 초기화"""
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb',region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Sessions')
    
    def create_session(self, session_data: SessionCreate) -> Session:
        """세션 생성"""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        session = Session(
            session_id=session_id,
            user_id=session_data.user_id,
            title=session_data.title,
            created_at=now,
            updated_at=now
        )
        
        item = {
            'user_id': session.user_id,
            'session_id': session.session_id,
            'title': session.title,
            'status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.message_count
        }
        
        db_start_time = time.time()
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Sessions "
                f"key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return session
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Sessions "
                f"key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_session_by_id(self, session_id: str, user_id: str) -> Optional[Session]:
        """세션 ID로 조회"""
        db_start_time = time.time()
        
        try:
            response = self.table.get_item(
                Key={'user_id': user_id, 'session_id': session_id}
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            item = response.get('Item')
            
            logger.info(
                f"db_operation=get_item "
                f"table=Sessions "
                f"key={session_id} "
                f"found={'yes' if item else 'no'} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not item or item.get('status') == SessionStatus.DELETED.value:
                return None
            
            return Session(
                session_id=item['session_id'],
                user_id=item['user_id'],
                title=item['title'],
                status=SessionStatus(item['status']),
                created_at=datetime.fromisoformat(item['created_at']),
                updated_at=datetime.fromisoformat(item['updated_at']),
                message_count=item['message_count']
            )
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=get_item "
                f"table=Sessions "
                f"key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """사용자의 세션 목록 조회 (최신순)"""        
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='UserUpdatedAtIndex',
                KeyConditionExpression=Key('user_id').eq(user_id),
                FilterExpression='#status <> :deleted',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':deleted': SessionStatus.DELETED.value},
                ScanIndexForward=False
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Sessions "
                f"index=UserUpdatedAtIndex "
                f"partition_key={user_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            sessions = []
            for item in items:
                sessions.append(Session(
                    session_id=item['session_id'],
                    user_id=item['user_id'],
                    title=item['title'],
                    status=SessionStatus(item['status']),
                    created_at=datetime.fromisoformat(item['created_at']),
                    updated_at=datetime.fromisoformat(item['updated_at']),
                    message_count=item['message_count']
                ))
            
            return sessions
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Sessions "
                f"index=UserUpdatedAtIndex "
                f"partition_key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def update_session_title(self, session_id: str, user_id: str, new_title: str) -> bool:
        """세션 제목 수정"""
        try:
            session = self.get_session_by_id(session_id, user_id)
            if not session:
                return False
            
            db_start_time = time.time()
            try:
                self.table.update_item(
                    Key={'user_id': user_id, 'session_id': session_id},
                    UpdateExpression='SET title = :title, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':title': new_title,
                        ':updated': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                db_duration = (time.time() - db_start_time) * 1000
                
                logger.info(
                    f"db_operation=update_item "
                    f"table=Sessions "
                    f"key={session_id} "
                    f"db_duration={db_duration:.2f}ms "
                    f"status=success"
                )
                
                return True
            
            except Exception as e:
                db_duration = (time.time() - db_start_time) * 1000
                
                logger.error(
                    f"db_operation=update_item "
                    f"table=Sessions "
                    f"key={session_id} "
                    f"db_duration={db_duration:.2f}ms "
                    f"status=failed "
                    f"error={str(e)}"
                )
                raise
        
        except Exception as e:
            logger.error(f"세션 수정 실패: {e}")
            return False

 
    def increment_message_count(self, session_id: str, user_id: str, increment: int = 1) -> None:
        """메시지 개수 증가"""
        db_start_time = time.time()
        
        try:
            self.table.update_item(
                Key={'user_id': user_id, 'session_id': session_id},
                UpdateExpression='SET updated_at = :updated ADD message_count :inc',
                ExpressionAttributeValues={
                    ':inc': increment,
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=update_item "
                f"table=Sessions "
                f"key={session_id} "
                f"action=increment_count "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=update_item "
                f"table=Sessions "
                f"key={session_id} "
                f"action=increment_count "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise

    def delete_session(self, session_id: str, user_id: str) -> None:
        """세션 status DELETE로 변경"""
        db_start_time = time.time()
        
        try:
            self.table.update_item(
                Key={'user_id': user_id, 'session_id': session_id},
                UpdateExpression='SET #status = :deleted, updated_at = :updated',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':deleted': SessionStatus.DELETED.value,
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=update_item "
                f"table=Sessions "
                f"key={session_id} "
                f"action=soft_delete "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=update_item "
                f"table=Sessions "
                f"key={session_id} "
                f"action=soft_delete "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise