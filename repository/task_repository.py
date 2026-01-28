"""
Task Repository
"""
import boto3
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from model.task import Task, TaskCreate, TaskType
from boto3.dynamodb.conditions import Key, Attr
from core.config import settings
import time
import logging

logger = logging.getLogger(__name__)


class TaskRepository:
    def __init__(self):
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Tasks')

    def _item_to_task(self, item: Dict) -> Task:
        """DynamoDB item을 Task 객체로 변환"""
        return Task(
            task_id=item['task_id'],
            user_id=item['user_id'],
            session_id=item['session_id'],
            task_type=TaskType(item['task_type']),
            success=bool(item['success']),
            created_at=datetime.fromisoformat(item['created_at'])
        )
    
    def create_task(self, data: TaskCreate) -> Task:
        """작업 생성"""
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        task = Task(
            task_id=task_id,
            session_id=data.session_id,
            user_id=data.user_id,
            task_type=data.task_type,
            success = data.success,
            created_at=now
        )
        
        item = {
            'task_id': task.task_id,
            'user_id': task.user_id,
            'session_id': task.session_id,
            'task_type': task.task_type.value,
            'success': task.success,
            'created_at': task.created_at.isoformat()
        }
        
        db_start_time = time.time()
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Tasks "
                f"key={task_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return task
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Tasks "
                f"key={task_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """task_id로 조회"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='TaskIdIndex',
                KeyConditionExpression=Key('task_id').eq(task_id)
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Tasks "
                f"index=TaskIdIndex "
                f"key={task_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not items:
                return None
            
            return self._item_to_task(items[0])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Tasks "
                f"index=TaskIdIndex "
                f"key={task_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    

    def get_session_tasks(self, session_id: str, limit: int = 20) -> List[Task]:
        """세션의 작업 목록 조회 (시간순)"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='SessionTasksIndex',
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=True,
                Limit=limit
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Tasks "
                f"index=SessionTasksIndex "
                f"partition_key={session_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_task(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Tasks "
                f"index=SessionTasksIndex "
                f"partition_key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise

    def get_user_tasks(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        task_type: Optional[TaskType] = None,
        success_only: Optional[bool] = None,
        limit: int = 100
    ) -> List[Task]:
        """사용자 작업 이력 조회 (필터링 가능)"""
        key_condition = Key('user_id').eq(user_id)
        
        # 날짜 범위 필터
        if start_date and end_date:
            key_condition = key_condition & Key('created_at').between(
                start_date.isoformat(),
                end_date.isoformat()
            )
        elif start_date:
            key_condition = key_condition & Key('created_at').gte(start_date.isoformat())
        elif end_date:
            key_condition = key_condition & Key('created_at').lte(end_date.isoformat())
        
        # FilterExpression 구성
        filter_expr = None
        if task_type:
            filter_expr = Attr('task_type').eq(task_type.value)
        if success_only is not None:
            success_filter = Attr('success').eq(success_only)
            filter_expr = success_filter if filter_expr is None else filter_expr & success_filter
        
        query_params = {
            'KeyConditionExpression': key_condition,
            'ScanIndexForward': False,  # 최신순
            'Limit': limit
        }
        
        if filter_expr:
            query_params['FilterExpression'] = filter_expr
        
        db_start_time = time.time()
        
        try:
            response = self.table.query(**query_params)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Tasks "
                f"partition_key={user_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_task(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Tasks "
                f"partition_key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_task_stats(self, user_id: str) -> Dict:
        """사용자 작업 통계"""
        tasks = self.get_user_tasks(user_id, limit=1000)  # 최근 1000개
        
        if not tasks:
            return {
                'total': 0,
                'success_count': 0,
                'success_rate': 0.0,
                'by_type': {}
            }
        
        total = len(tasks)
        success_count = sum(1 for t in tasks if t.success)
        success_rate = round((success_count / total) * 100, 2)
        
        # 작업 유형별 통계
        by_type = {}
        for task in tasks:
            type_str = task.task_type.value
            if type_str not in by_type:
                by_type[type_str] = {'total': 0, 'success': 0}
            by_type[type_str]['total'] += 1
            if task.success:
                by_type[type_str]['success'] += 1

        for type_str in by_type:
            type_str_total_count = by_type[type_str]['total']
            type_str_success_count = by_type[type_str]['success']
            print(f"success_count :  {success_count}")
            by_type[type_str]['success_rate'] = round((type_str_success_count / type_str_total_count) * 100, 2)

            
        return {
            'total': total,
            'success_count': success_count,
            'success_rate': success_rate,
            'by_type': by_type
        }
    
    def update_task_status(self, task_id: str, success: bool) -> Optional[Task]:
        """작업 상태 업데이트"""
        
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        db_start_time = time.time()
        
        try:
            response = self.table.update_item(
                Key={
                    'user_id': task.user_id,
                    'created_at': task.created_at.isoformat()
                },
                UpdateExpression='SET success = :success',
                ExpressionAttributeValues={':success': success},
                ReturnValues='ALL_NEW'
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=update_item "
                f"table=Tasks "
                f"key={task_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return self._item_to_task(response['Attributes'])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=update_item "
                f"table=Tasks "
                f"key={task_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise