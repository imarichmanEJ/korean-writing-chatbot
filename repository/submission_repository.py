"""
Submission Repository
"""
import boto3
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from model.submission import Submission, SubmissionCreate, QuestionType, BlankType
from core.config import settings
from boto3.dynamodb.conditions import Key, Attr
import time
import logging

logger = logging.getLogger(__name__)

class SubmissionRepository:
    def __init__(self):
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Submissions')

    def _item_to_submission(self, item: Dict) -> Submission:
        """DynamoDB item을 Submission 객체로 변환"""
        return Submission(
            submission_id=item['submission_id'],
            user_id=item['user_id'],
            question_id=item['question_id'],
            session_id=item['session_id'],
            answer=item['answer'],
            question_type=QuestionType(item['question_type']),
            blank_type=BlankType(item['blank_type']) if item.get('blank_type') else None,
            submitted_at=datetime.fromisoformat(item['submitted_at'])
        )
    
    def create_submission(self, submission_data: SubmissionCreate) -> Submission:
        """답안 제출 생성"""
        submission_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        submission = Submission(
            submission_id=submission_id,
            user_id=submission_data.user_id,
            question_id=submission_data.question_id,
            session_id=submission_data.session_id,
            answer=submission_data.answer,
            question_type=submission_data.question_type,
            blank_type=submission_data.blank_type,
            submitted_at=now
        )
        
        item = {
            'submission_id': submission.submission_id,
            'user_id': submission.user_id,
            'question_id': submission.question_id,
            'session_id': submission.session_id,
            'answer': submission.answer,
            'question_type': submission.question_type.value,
            'submitted_at': submission.submitted_at.isoformat()
        }
        
        if submission.blank_type:
            item['blank_type'] = submission.blank_type.value
        
        db_start_time = time.time()
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Submissions "
                f"key={submission_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return submission
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Submissions "
                f"key={submission_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_submission_by_id(self, submission_id: str) -> Optional[Submission]:
        """submission_id로 단일 답안 조회"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='SubmissionIdIndex',
                KeyConditionExpression=Key('submission_id').eq(submission_id)
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Submissions "
                f"index=SubmissionIdIndex "
                f"key={submission_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not items:
                return None
            
            return self._item_to_submission(items[0])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Submissions "
                f"index=SubmissionIdIndex "
                f"key={submission_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_submissions(
        self,
        user_id: str,
        question_type: Optional[str] = None,
        blank_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Submission]:
        """사용자 답안 조회 (question_type/blank_type 필터 가능)"""
        
        filter_expr = None
        if question_type:
            filter_expr = Attr('question_type').eq(question_type)
        if blank_type:
            blank_filter = Attr('blank_type').eq(blank_type)
            if filter_expr is None:
                filter_expr = blank_filter
            else:
                filter_expr = filter_expr & blank_filter
        
        query_params = {
            'KeyConditionExpression': Key('user_id').eq(user_id),
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
                f"table=Submissions "
                f"partition_key={user_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_submission(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Submissions "
                f"partition_key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_submissions_by_question(
        self,
        question_id: str,
        limit: int = 100
    ) -> List[Submission]:
        """question_id에 대한 답안 목록 조회"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='QuestionSubmissionsIndex',
                KeyConditionExpression=Key('question_id').eq(question_id),
                ScanIndexForward=False,  # 최신순
                Limit=limit
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Submissions "
                f"index=QuestionSubmissionsIndex "
                f"partition_key={question_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_submission(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Submissions "
                f"index=QuestionSubmissionsIndex "
                f"partition_key={question_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
