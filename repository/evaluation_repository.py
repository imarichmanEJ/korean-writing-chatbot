"""
Evaluation Repository
"""
import boto3
import uuid
from typing import List, Optional, Dict
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr
from model.evaluation import Evaluation, EvaluationCreate, QuestionType
from core.config import settings
from decimal import Decimal
import time
import logging

logger = logging.getLogger(__name__)

class EvaluationRepository:
    def __init__(self):
        if settings.DYNAMODB_ENDPOINT:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=settings.DYNAMODB_ENDPOINT,
                region_name=settings.AWS_REGION
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        
        self.table = self.dynamodb.Table('Evaluations')

    def _item_to_evaluation(self, item: Dict) -> Evaluation:
        """DynamoDB item을 Evaluation 객체로 변환"""
        return Evaluation(
            evaluation_id=item['evaluation_id'],
            submission_id=item['submission_id'],
            session_id=item['session_id'],
            user_id=item['user_id'],
            question_id=item['question_id'],
            question_type=QuestionType(item['question_type']),
            total_score=float(item['total_score']),
            con_score=float(item['con_score']) if item.get('con_score') else None,
            org_score=float(item['org_score']) if item.get('org_score') else None,
            exp_score=float(item['exp_score']) if item.get('exp_score') else None,
            feedback=item['feedback'],
            created_at=datetime.fromisoformat(item['created_at'])
        )
    
    def create_evaluation(self, evaluation_data: EvaluationCreate) -> Evaluation:
        """채점 생성"""
        evaluation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        evaluation = Evaluation(
            evaluation_id=evaluation_id,
            submission_id=evaluation_data.submission_id,
            session_id=evaluation_data.session_id,
            user_id=evaluation_data.user_id,
            question_id=evaluation_data.question_id,
            question_type=evaluation_data.question_type,
            total_score=evaluation_data.total_score,
            con_score=evaluation_data.con_score,
            org_score=evaluation_data.org_score,
            exp_score=evaluation_data.exp_score,
            feedback=evaluation_data.feedback,
            created_at=now
        )
        
        item = {
            'evaluation_id': evaluation.evaluation_id,
            'submission_id': evaluation.submission_id,
            'session_id' : evaluation.session_id,
            'user_id': evaluation.user_id,
            'question_id': evaluation.question_id,
            'question_type': evaluation.question_type.value,
            'total_score': Decimal(str(evaluation.total_score)),
            'feedback': evaluation.feedback,
            'created_at': evaluation.created_at.isoformat()
        }
        
        if evaluation.con_score is not None:
            item['con_score'] = Decimal(str(evaluation.con_score))
        if evaluation.org_score is not None:
            item['org_score'] = Decimal(str(evaluation.org_score))
        if evaluation.exp_score is not None:
            item['exp_score'] = Decimal(str(evaluation.exp_score))
        
        db_start_time = time.time()
        try:
            self.table.put_item(Item=item)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.info(
                f"db_operation=put_item "
                f"table=Evaluations "
                f"key={evaluation_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return evaluation
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=put_item "
                f"table=Evaluations "
                f"key={evaluation_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_evaluation_by_id(self, evaluation_id: str) -> Optional[Evaluation]:
        """evaluation_id로 단일 채점 조회"""
        db_start_time = time.time()
        try:
            response = self.table.query(
                IndexName='EvaluationIdIndex',
                KeyConditionExpression=Key('evaluation_id').eq(evaluation_id)
            )
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=EvaluationIdIndex "
                f"key={evaluation_id} "
                f"evaluation_id={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            if not items:
                return None
            
            return self._item_to_evaluation(items[0])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=EvaluationIdIndex "
                f"key={evaluation_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_evaluation_by_submission(self, submission_id: str) -> Optional[Evaluation]:
        """submission_id로 채점 조회"""
        db_start_time = time.time()
        try:
            response = self.table.query(
                IndexName='SubmissionEvaluationIndex',
                KeyConditionExpression=Key('submission_id').eq(submission_id)
            )
            db_duration = (time.time() - db_start_time) * 1000

            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=SubmissionEvaluationIndex "
                f"key={submission_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )

            if not items:
                return None
            
            return self._item_to_evaluation(items[0])
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=SubmissionEvaluationIndex "
                f"key={submission_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    
    def get_user_evaluations(
        self,
        user_id: str,
        question_type: Optional[QuestionType] = None,
        limit: int = 100
    ) -> List[Evaluation]:
        """사용자 채점 이력 조회 (question_type 필터 가능)"""
        
        query_params = {
            'KeyConditionExpression': Key('user_id').eq(user_id),
            'ScanIndexForward': False,  # 최신순
            'Limit': limit
        }
        
        if question_type:
            query_params['FilterExpression'] = Attr('question_type').eq(question_type.value)        

        db_start_time = time.time()
        try:
            response = self.table.query(**query_params)
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Evaluations "
                f"partition_key={user_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_evaluation(item) for item in items]
        
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Evaluations "
                f"partition_key={user_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise
    


    def get_session_evaluations(self, session_id: str, limit: int = 100) -> List[Evaluation]:
        """세션별 평가 조회 (새 메서드)"""
        db_start_time = time.time()
        
        try:
            response = self.table.query(
                IndexName='SessionEvaluationIndex',
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,
                Limit=limit
            )
            
            db_duration = (time.time() - db_start_time) * 1000
            
            items = response.get('Items', [])
            
            logger.info(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=SessionEvaluationIndex "
                f"partition_key={session_id} "
                f"result_count={len(items)} "
                f"db_duration={db_duration:.2f}ms "
                f"status=success"
            )
            
            return [self._item_to_evaluation(item) for item in items]
        except Exception as e:
            db_duration = (time.time() - db_start_time) * 1000
            
            logger.error(
                f"db_operation=query "
                f"table=Evaluations "
                f"index=SessionEvaluationIndex "
                f"partition_key={session_id} "
                f"db_duration={db_duration:.2f}ms "
                f"status=failed "
                f"error={str(e)}"
            )
            raise

    def get_user_score_stats(self, user_id: str) -> Dict:
        """사용자 점수 통계"""
        evaluations = self.get_user_evaluations(user_id, limit=1000)
        
        if not evaluations:
            return {
                'total_count': 0,
                'average_score': 0.0,
                'highest_score': 0.0,
                'lowest_score': 0.0,
                'by_question_type': {}
            }
        
        total_count = len(evaluations)
        total_score_sum = sum(e.total_score for e in evaluations)
        average_score = total_score_sum / total_count
        highest_score = max(e.total_score for e in evaluations)
        lowest_score = min(e.total_score for e in evaluations)
        
        # question_type별 통계
        by_type = {}
        for evaluation in evaluations:
            type_str = evaluation.question_type.value
            if type_str not in by_type:
                by_type[type_str] = {
                    'count': 0,
                    'total_score_sum': 0.0,
                    'scores': []
                }
            by_type[type_str]['count'] += 1
            by_type[type_str]['total_score_sum'] += evaluation.total_score
            by_type[type_str]['scores'].append(evaluation.total_score)
        
        # 평균 계산
        for type_str in by_type:
            count = by_type[type_str]['count']
            by_type[type_str]['average_score'] = round(
                by_type[type_str]['total_score_sum'] / count, 2
            )
            by_type[type_str]['highest_score'] = max(by_type[type_str]['scores'])
            by_type[type_str]['lowest_score'] = min(by_type[type_str]['scores'])
            del by_type[type_str]['scores']
            del by_type[type_str]['total_score_sum']
        
        return {
            'total_count': total_count,
            'average_score': round(average_score, 2),
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'by_question_type': by_type
        }