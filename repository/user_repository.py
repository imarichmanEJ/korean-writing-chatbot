"""
User Repository
"""
import boto3
from typing import Optional
from datetime import datetime, timezone
import uuid
from model.user import User, UserCreate, UserRole
from core.config import settings
from boto3.dynamodb.conditions import Key
import time
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        """DynamoDB 연결 초기화"""
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)        
        self.table = self.dynamodb.Table('Users')
    
    def create_user(self, user_data: UserCreate) -> User:
        """사용자 생성"""

        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"이미 존재하는 이름입니다: {user_data.username}")
        
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        user = User(
            user_id=user_id,
            email=user_data.email,
            username=user_data.username,
            role=user_data.role,
            created_at=now
        )
        
        item = {
            'user_id': user.user_id,
            'email': user.email,
            'username': user.username,
            'role': user.role.value,
            'created_at': user.created_at.isoformat()
        }

        if user.last_login:
            item['last_login'] = user.last_login.isoformat()

        db_start_time = time.time()
        
        try:
            self.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(user_id)"
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Users "
                f"key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return user
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Users "
                f"key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """user_id로 조회"""
        db_start_time = time.time()
        
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            
            db_duration = (time.time() - db_start_time) * 1000
            
            item = response.get('Item')
            
            logger.info(
                f"db_operation=get_item "
                f"table=Users "
                f"key={user_id} "
                f"found={'yes' if item else 'no'} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not item:
                return None
            
            return User(
                user_id=item['user_id'],
                email=item['email'],
                username=item['username'],
                role=UserRole(item['role']),
                created_at=datetime.fromisoformat(item['created_at']),
                last_login=datetime.fromisoformat(item['last_login']) if item.get('last_login') else None
            )
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=get_item "
                f"table=Users "
                f"key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """email로 조회 (GSI)"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='EmailIndex',
                KeyConditionExpression=Key('email').eq(email)
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Users "
                f"index=EmailIndex "
                f"key={email} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not items:
                return None
            
            item = items[0]
            return User(
                user_id=item['user_id'],
                email=item['email'],
                username=item['username'],
                role=UserRole(item['role']),
                created_at=datetime.fromisoformat(item['created_at']),
                last_login=datetime.fromisoformat(item['last_login']) if item.get('last_login') else None
            )
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Users "
                f"index=EmailIndex "
                f"key={email} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def update_last_login(self, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트"""
        db_start_time = time.time()
        
        try:
            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET last_login = :login',
                ExpressionAttributeValues={
                    ':login': datetime.now(timezone.utc).isoformat()
                }
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=update_item "
                f"table=Users "
                f"key={user_id} "
                f"action=update_last_login "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return True
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=update_item "
                f"table=Users "
                f"key={user_id} "
                f"action=update_last_login "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            return False