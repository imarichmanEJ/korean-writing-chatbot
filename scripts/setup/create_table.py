"""
scripts/setup/create_table.py " DynamoDB 테이블 생성 스크립트
python infrastructure/create_table.py --env local
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import boto3
from botocore.exceptions import ClientError
from core.config import settings
import time


#users 테이블 생성
def create_users_table(dynamodb_endpoint: str = None) -> dict:
    """Users 테이블 생성"""
    
    if dynamodb_endpoint:
        print("→ 로컬 DynamoDB 연결")
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        print("→ AWS DynamoDB 연결")
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Users'
    
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        return {'exists': True, 'table': existing['Table']}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
        else:
            raise
    
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"   ✓ 생성 요청 전송 완료")
    except ClientError as e:
        print(f"   ✗ 생성 실패: {e}")
        raise
    
    print(f"\n3. 테이블 활성화 대기 중...")
    time.sleep(1)
    
    try:
        table_info = dynamodb.describe_table(TableName=table_name)
        print(f"   ✓ 테이블 활성화 완료!")
    except ClientError as e:
        print(f"   ✗ 검증 실패: {e}")
        raise
    
    print("\n" + "=" * 50)
    print("✓ 테이블 생성 완료!")
    print("=" * 50)
    print(f"[테이블 정보]")
    print(f"  - 이름: {table_name}")
    print(f"  - PK: user_id (HASH)")
    print(f"  - GSI: EmailIndex (email)")
    print("=" * 50)
    
    return response


#Sessions 테이블 생성
def create_sessions_table(dynamodb_endpoint: str = None) -> dict:

    # DynamoDB 클라이언트 생성
    if dynamodb_endpoint:
        print("→ 로컬 DynamoDB 연결")
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        print("→ AWS DynamoDB 연결")
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Sessions'
    
    # ========================================
    # 1. 테이블 존재 여부 확인
    # ========================================
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        print(f"   - 상태: {existing['Table']['TableStatus']}")
        print(f"   - 생성일: {existing['Table']['CreationDateTime']}")
        return {'exists': True, 'table': existing['Table']}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
        else:
            print(f"   ✗ 확인 중 에러: {e}")
            raise
    
    # ========================================
    # 2. 테이블 생성
    # ========================================
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'session_id', 'KeyType': 'RANGE'}
            ],
            
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
                {'AttributeName': 'updated_at', 'AttributeType': 'S'},
            ],
            
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserUpdatedAtIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'updated_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"   ✓ 생성 요청 전송 완료")
        
    except ClientError as e:
        print(f"   ✗ 생성 실패: {e}")
        print(f"   - 에러 코드: {e.response['Error']['Code']}")
        print(f"   - 메시지: {e.response['Error']['Message']}")
        raise
    
    # ========================================
    # 3. 생성 완료 대기 및 검증
    # ========================================
    print(f"\n3. 테이블 활성화 대기 중...")
    time.sleep(1)  # 로컬은 즉시, AWS는 더 길 수 있음
    
    try:
        table_info = dynamodb.describe_table(TableName=table_name)
        table_status = table_info['Table']['TableStatus']
        
        if table_status == 'ACTIVE':
            print(f"   ✓ 테이블 활성화 완료!")
        else:
            print(f"   → 현재 상태: {table_status}")
        
    except ClientError as e:
        print(f"   ✗ 검증 실패: 테이블을 찾을 수 없음")
        print(f"   - 에러: {e}")
        raise
    
    # ========================================
    # 4. 최종 확인 (list_tables로 재검증)
    # ========================================
    print(f"\n4. 테이블 목록 재확인...")
    list_response = dynamodb.list_tables()
    all_tables = list_response['TableNames']
    
    if table_name in all_tables:
        print(f"   ✓ '{table_name}' 테이블 목록에서 확인됨")
    else:
        print(f"   ✗ 경고: 테이블이 목록에 없음")
        print(f"   - 전체 목록: {all_tables}")
    
    # ========================================
    # 5. 테이블 정보 출력
    # ========================================
    print("\n" + "=" * 50)
    print("✓ 테이블 생성 완료!")
    print("=" * 50)
    print(f"[테이블 정보]")
    print(f"  - 이름: {table_name}")
    print(f"  - 상태: {table_info['Table']['TableStatus']}")
    print(f"  - PK: user_id (HASH)")
    print(f"  - SK: session_id (RANGE)")
    print(f"  - GSI: SessionIdIndex (session_id)")
    print(f"  - 과금: PAY_PER_REQUEST")
    print("=" * 50)
    
    return response


#Messages 테이블 생성
def create_messages_table(dynamodb_endpoint: str = None) -> dict:

    # DynamoDB 클라이언트 생성
    if dynamodb_endpoint:
        print("→ 로컬 DynamoDB 연결")
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        print("→ AWS DynamoDB 연결")
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Messages'
    
    # ========================================
    # 1. 기존 테이블 확인
    # ========================================
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        print(f"   - 상태: {existing['Table']['TableStatus']}")
        return {'exists': True, 'table': existing['Table']}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
        else:
            print(f"   ✗ 확인 중 에러: {e}")
            raise
    
    # ========================================
    # 2. 테이블 생성
    # ========================================
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            
            # 키 구조
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},   # PK
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}    # SK
            ],
            
            # 속성 정의
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            ],
            
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"   ✓ 생성 요청 전송 완료")
        
    except ClientError as e:
        print(f"   ✗ 생성 실패: {e}")
        raise
    
    # ========================================
    # 3. 생성 완료 대기 및 검증
    # ========================================
    print(f"\n3. 테이블 활성화 대기 중...")
    time.sleep(1)
    
    try:
        table_info = dynamodb.describe_table(TableName=table_name)
        table_status = table_info['Table']['TableStatus']
        
        if table_status == 'ACTIVE':
            print(f"   ✓ 테이블 활성화 완료!")
        else:
            print(f"   → 현재 상태: {table_status}")
        
    except ClientError as e:
        print(f"   ✗ 검증 실패: {e}")
        raise
    
    # ========================================
    # 4. 최종 확인
    # ========================================
    print(f"\n4. 테이블 목록 재확인...")
    list_response = dynamodb.list_tables()
    all_tables = list_response['TableNames']
    
    if table_name in all_tables:
        print(f"   ✓ '{table_name}' 테이블 목록에서 확인됨")
    else:
        print(f"   ✗ 경고: 테이블이 목록에 없음")
    
    # ========================================
    # 5. 테이블 정보 출력
    # ========================================
    print("\n" + "=" * 50)
    print("✓ 테이블 생성 완료!")
    print("=" * 50)
    print(f"[테이블 정보]")
    print(f"  - 이름: {table_name}")
    print(f"  - 상태: {table_info['Table']['TableStatus']}")
    print(f"  - PK: session_id (HASH)")
    print(f"  - SK: timestamp (RANGE)")
    print(f"  - 과금: PAY_PER_REQUEST")
    print("=" * 50)
    
    return response


#tasks 테이블 생성
def create_tasks_table(dynamodb_endpoint: str = None) -> dict:
    """Tasks 테이블 생성"""
    
    if dynamodb_endpoint:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Tasks'
    
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        return {'exists': True}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
    
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    response = dynamodb.create_table(
        TableName='Tasks',
        
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
        ],
        
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'session_id', 'AttributeType': 'S'},
            {'AttributeName': 'task_id', 'AttributeType': 'S'}
        ],
        
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'SessionTasksIndex',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'TaskIdIndex',
                'KeySchema': [
                    {'AttributeName': 'task_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        
        BillingMode='PAY_PER_REQUEST'
    )
    
    time.sleep(1)
    print(f"   ✓ 테이블 생성 완료!")
    return response


#questions 테이블 생성
def create_questions_table(dynamodb_endpoint: str = None) -> dict:
    """Questions 테이블 생성"""
    
    if dynamodb_endpoint:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Questions'
    
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        return {'exists': True}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
    
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    response = dynamodb.create_table(
        TableName='Questions',
        
        KeySchema=[
            {'AttributeName': 'session_id', 'KeyType': 'HASH'},
            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
        ],
        
        AttributeDefinitions=[
            {'AttributeName': 'session_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'question_id', 'AttributeType': 'S'}
        ],
        
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'QuestionIdIndex',
                'KeySchema': [
                    {'AttributeName': 'question_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        
        BillingMode='PAY_PER_REQUEST'
    )
    
    time.sleep(1)
    print(f"   ✓ 테이블 생성 완료!")
    return response


#submissions 테이블 생성
def create_submissions_table(dynamodb_endpoint: str = None) -> dict:
    """Submissions 테이블 생성"""
    
    if dynamodb_endpoint:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Submissions'
    
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        return {'exists': True}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
    
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    response = dynamodb.create_table(
        TableName='Submissions',
        
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'}
        ],

        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'submitted_at', 'AttributeType': 'S'},
            {'AttributeName': 'submission_id', 'AttributeType': 'S'},
            {'AttributeName': 'question_id', 'AttributeType': 'S'}
        ],

        GlobalSecondaryIndexes=[
            {
                'IndexName': 'SubmissionIdIndex',
                'KeySchema': [
                    {'AttributeName': 'submission_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'QuestionSubmissionsIndex',
                'KeySchema': [
                    {'AttributeName': 'question_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'submitted_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        
        BillingMode='PAY_PER_REQUEST'
    )
    
    time.sleep(1)
    print(f"   ✓ 테이블 생성 완료!")
    return response


#evaluations 테이블 생성
def create_evaluations_table(dynamodb_endpoint: str = None) -> dict:
    """Evaluations 테이블 생성"""
    
    if dynamodb_endpoint:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=dynamodb_endpoint,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
    else:
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    
    table_name = 'Evaluations'
    
    print(f"\n1. 기존 테이블 확인 중...")
    try:
        existing = dynamodb.describe_table(TableName=table_name)
        print(f"   ! 테이블 '{table_name}'이 이미 존재합니다")
        return {'exists': True}
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"   → 테이블 없음, 새로 생성합니다")
    
    print(f"\n2. 테이블 '{table_name}' 생성 중...")
    response = dynamodb.create_table(
        TableName='Evaluations',
        
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
        ],
        
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'evaluation_id', 'AttributeType': 'S'},
            {'AttributeName': 'submission_id', 'AttributeType': 'S'},
            {'AttributeName': 'session_id', 'AttributeType': 'S'}
        ],
        
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'EvaluationIdIndex',
                'KeySchema': [
                    {'AttributeName': 'evaluation_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'SubmissionEvaluationIndex',
                'KeySchema': [
                    {'AttributeName': 'submission_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'SessionEvaluationIndex',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        
        BillingMode='PAY_PER_REQUEST'
    )
    
    time.sleep(1)
    print(f"   ✓ 테이블 생성 완료!")
    return response




#메인 실행 함수
def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DynamoDB 테이블 생성')
    parser.add_argument(
        '--env',
        choices=['local', 'aws'],
        default='local',
        help='환경 선택'
    )
    parser.add_argument(
        '--table',
        choices=['users', 'sessions', 'messages', 'tasks', 'questions', 'submissions', 'evaluations', 'all'],
        default='all',
        help='생성할 테이블 선택'
    )
    args = parser.parse_args()
    
    print("=" * 50)
    print("DynamoDB 테이블 생성")
    print("=" * 50)
    print(f"환경: {args.env}")
    print(f"Region: {settings.AWS_REGION}")
    
    if args.env == 'local':
        endpoint = settings.DYNAMODB_ENDPOINT  # config.py에서 가져옴
    else:
        endpoint = None
    
    print(f"Endpoint: {endpoint or 'AWS DynamoDB'}")
    print(f"생성 대상: {args.table}")
    print("=" * 50)
    
    try:
        if args.table in ['users', 'all']:
            print("\n[Users 테이블]")
            create_users_table(endpoint)
            
        if args.table in ['sessions', 'all']:
            print("\n[Sessions 테이블]")
            create_sessions_table(endpoint)
        
        if args.table in ['messages', 'all']:
            print("\n[Messages 테이블]")
            create_messages_table(endpoint)
                
        if args.table in ['tasks', 'all']:
            print("\n[Tasks 테이블]")
            create_tasks_table(endpoint)
        
        if args.table in ['questions', 'all']:
            print("\n[Questions 테이블]")
            create_questions_table(endpoint)
            
        if args.table in ['submissions', 'all']:
            print("\n[Submissions 테이블]")
            create_submissions_table(endpoint)
        
        if args.table in ['evaluations', 'all']:
            print("\n[Evaluations 테이블]")
            create_evaluations_table(endpoint)
                
        print("\n" + "=" * 50)
        print("✓ 모든 테이블 생성 완료!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 테이블 생성 실패")
        print(f"에러: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())