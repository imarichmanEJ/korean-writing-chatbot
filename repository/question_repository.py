"""
Question Repository
"""
import boto3
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from model.question import Question, QuestionCreate, QuestionType, Difficulty, BlankType, BlankData
from core.config import settings
from boto3.dynamodb.conditions import Key, Attr

import time
import logging
logger = logging.getLogger(__name__) 


class QuestionRepository:
    def __init__(self):
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Questions')

    def _item_to_question(self, item: Dict) -> Question:
        
        blank_data = None
        if item.get('blank_data'):
            blank_data = BlankData(**item['blank_data'])
        
        return Question(
            question_id=item['question_id'],
            session_id=item['session_id'],
            question_type=QuestionType(item['question_type']),
            difficulty=Difficulty(item['difficulty']),
            question=item.get('question'),
            blank_type=BlankType(item['blank_type']) if item.get('blank_type') else None,
            blank_data=blank_data,
            created_at=datetime.fromisoformat(item['created_at']),
            version=item.get('version', 1)
        )
    
    def create_question(self, data: QuestionCreate) -> Question:
        """문제 생성"""
        question_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        question = Question(
            question_id=question_id,
            session_id=data.session_id,
            question_type=data.question_type,
            difficulty=data.difficulty,
            question=data.question,
            blank_type=data.blank_type,
            blank_data=data.blank_data,
            created_at=now
        )
        
        item = {
            'question_id': question.question_id,
            'session_id': question.session_id,
            'question' : question.question,
            'question_type': question.question_type.value,
            'difficulty': question.difficulty.value,
            'created_at': question.created_at.isoformat(),
            'version': question.version
        }

        if question.blank_type:
            item['blank_type'] = question.blank_type.value
        if question.blank_data:
            item['blank_data'] = question.blank_data    

        db_start_time = time.time()
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Questions "
                f"key={question_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return question
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Questions "
                f"key={question_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """question_id로 단일 문제 조회"""

        db_start_time = time.time()
        try:
            response = self.table.query(
                IndexName='QuestionIdIndex',
                KeyConditionExpression=Key('question_id').eq(question_id)
            )
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Questions "
                f"index=QuestionIdIndex "
                f"key={question_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not items:
                return None
            
            return self._item_to_question(items[0])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Questions "
                f"index=QuestionIdIndex "
                f"key={question_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_session_questions(
            self,
            session_id: str,
            question_type: Optional[str] = None,
            blank_type: Optional[str] = None,
            difficulty: Optional[str] = None
        ) -> List[Question]:
            """세션의 문제 목록 조회 (필터링 가능)"""
            
            # FilterExpression 동적 구성
            filter_expr = None
            if question_type:
                filter_expr = Attr('question_type').eq(question_type)
            if blank_type:
                blank_filter = Attr('blank_type').eq(blank_type)
                filter_expr = blank_filter if filter_expr is None else filter_expr & blank_filter
            if difficulty:
                diff_filter = Attr('difficulty').eq(difficulty)
                filter_expr = diff_filter if filter_expr is None else filter_expr & diff_filter
            
            query_params = {
                'KeyConditionExpression': Key('session_id').eq(session_id),
                'ScanIndexForward': True
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
                    f"table=Questions "
                    f"partition_key={session_id} "
                    f"result_count={len(items)} "
                    f"db_duration={db_duration:.2f}ms "
                    f"status=success"
                )
                
                return [self._item_to_question(item) for item in items]
            
            except Exception as e:
                db_duration = (time.time() - db_start_time) * 1000
                
                logger.error(
                    f"db_operation=query "
                    f"table=Questions "
                    f"partition_key={session_id} "
                    f"db_duration={db_duration:.2f}ms "
                    f"status=failed "
                    f"error={str(e)}"
                )
                raise