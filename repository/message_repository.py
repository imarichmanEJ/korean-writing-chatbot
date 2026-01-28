"""
Message Repository
DynamoDB Messages 테이블 CRUD
"""
import boto3
from typing import List
from datetime import datetime, timezone
import uuid
from model.message import Message, MessageCreate, MessageRole
from core.config import settings
from boto3.dynamodb.conditions import Key
import time
import logging

logger = logging.getLogger(__name__)


class MessageRepository:
    def __init__(self):
        """DynamoDB 연결 초기화"""
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Messages')

    def _item_to_message(self, item: dict) -> Message:
        """DynamoDB item을 Message 객체로 변환"""
        return Message(
            message_id=item['message_id'],
            session_id=item['session_id'],
            role=MessageRole(item['role']),
            content=item['content'],
            timestamp=datetime.fromisoformat(item['timestamp'])
        )
    
    def create_message(self, message_data: MessageCreate) -> Message:
        """메시지 추가"""
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        message = Message(
            message_id=message_id,
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            timestamp=now
        )

        item = {
            'message_id': message.message_id,
            'session_id': message.session_id,
            'role': message.role.value,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        }
        
        db_start_time = time.time()
        
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Messages "
                f"key={message_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return message
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Messages "
                f"key={message_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_session_messages(
            self, 
            session_id: str, 
            limit: int = 50, 
            ascending: bool = True
        ) -> List[Message]:
        """세션의 메시지 목록 조회 (시간순)"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=ascending,
                Limit=limit
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Messages "
                f"partition_key={session_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_message(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Messages "
                f"partition_key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    
    # def get_messages_in_time_range(self, session_id: str, start_time: datetime, end_time: datetime) -> List[Message]:
    #     """시간 범위로 메시지 조회 (AP2)"""
    #     response = self.table.query(
    #         KeyConditionExpression='session_id = :sid AND #ts BETWEEN :start AND :end',
    #         ExpressionAttributeNames={'#ts': 'timestamp'},
    #         ExpressionAttributeValues={
    #             ':sid': session_id,
    #             ':start': start_time.isoformat(),
    #             ':end': end_time.isoformat()
    #         }
    #     )
        
    #     messages = []
    #     for item in response.get('Items', []):
    #         messages.append(Message(
    #             message_id=item['message_id'],
    #             session_id=item['session_id'],
    #             role=MessageRole(item['role']),
    #             content=item['content'],
    #             timestamp=datetime.fromisoformat(item['timestamp']),
    #             metadata=item.get('metadata', {})
    #         ))
        
    #     return messages
    
    # def get_recent_messages(self, session_id: str, count: int = 10) -> List[Message]:
    #     """최근 N개 메시지 조회 (간편 메서드)"""
    #     return self.get_session_messages(
    #         session_id=session_id,
    #         limit=count,
    #         ascending=False
    #     )
    
    # def count_messages(self, session_id: str) -> int:
    #     """세션의 총 메시지 개수 조회"""
    #     response = self.table.query(
    #         KeyConditionExpression='session_id = :sid',
    #         ExpressionAttributeValues={':sid': session_id},
    #         Select='COUNT'
    #     )
        
    #     return response.get('Count', 0)
    
    # def delete_session_messages(self, session_id: str) -> int:
    #     """세션의 모든 메시지 삭제"""
    #     # 1. 메시지 목록 조회
    #     messages = self.get_session_messages(session_id, limit=1000)
        
    #     # 2. 일괄 삭제
    #     deleted_count = 0
    #     with self.table.batch_writer() as batch:
    #         for message in messages:
    #             batch.delete_item(
    #                 Key={
    #                     'session_id': message.session_id,
    #                     'timestamp': message.timestamp.isoformat()
    #                 }
    #             )
    #             deleted_count += 1
        
    #     return deleted_count