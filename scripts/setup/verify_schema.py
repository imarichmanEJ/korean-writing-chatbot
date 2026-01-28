"""
DynamoDB 스키마 검증 스크립트
python scripts/setup/verify_schema.py --env local
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import boto3
from core.config import settings
import argparse


def verify_tables(dynamodb_endpoint: str = None):
    """모든 테이블의 스키마 검증"""
    
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
    
    TABLE_NAMES = [
        'Users',
        'Sessions', 
        'Messages',
        'Tasks',
        'Questions',
        'Submissions',
        'Evaluations'
    ]
    
    print("\n" + "="*70)
    print("DynamoDB 스키마 검증")
    print("="*70)
    
    missing_tables = []
    
    for table_name in TABLE_NAMES:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            table_info = response['Table']
            
            print(f"\n{'='*70}")
            print(f"테이블: {table_name}")
            print(f"{'='*70}")
            print(f"상태: {table_info['TableStatus']}")
            print(f"생성일: {table_info['CreationDateTime']}")
            
            # Keys
            print("\n[키 구조]")
            for key in table_info['KeySchema']:
                key_name = key['AttributeName']
                key_type = key['KeyType']
                attr_type = next(
                    attr['AttributeType'] 
                    for attr in table_info['AttributeDefinitions'] 
                    if attr['AttributeName'] == key_name
                )
                key_type_kr = "Partition Key" if key_type == "HASH" else "Sort Key"
                print(f"  {key_type_kr}: {key_name} ({attr_type})")
            
            # GSI
            if 'GlobalSecondaryIndexes' in table_info:
                print("\n[Global Secondary Indexes]")
                for gsi in table_info['GlobalSecondaryIndexes']:
                    print(f"  ┌─ {gsi['IndexName']}")
                    for key in gsi['KeySchema']:
                        key_type_kr = "PK" if key['KeyType'] == "HASH" else "SK"
                        print(f"  │  {key_type_kr}: {key['AttributeName']}")
                    print(f"  └─ Projection: {gsi['Projection']['ProjectionType']}")
            else:
                print("\n[Global Secondary Indexes]")
                print("  (없음)")
            
            # LSI
            if 'LocalSecondaryIndexes' in table_info:
                print("\n[Local Secondary Indexes]")
                for lsi in table_info['LocalSecondaryIndexes']:
                    print(f"  ┌─ {lsi['IndexName']}")
                    for key in lsi['KeySchema']:
                        key_type_kr = "PK" if key['KeyType'] == "HASH" else "SK"
                        print(f"  │  {key_type_kr}: {key['AttributeName']}")
                    print(f"  └─ Projection: {lsi['Projection']['ProjectionType']}")
            
            # TTL
            try:
                ttl_response = dynamodb.describe_time_to_live(TableName=table_name)
                ttl_status = ttl_response['TimeToLiveDescription']['TimeToLiveStatus']
                
                print("\n[TTL]")
                if ttl_status == 'ENABLED':
                    ttl_attr = ttl_response['TimeToLiveDescription']['AttributeName']
                    print(f"  활성화: {ttl_attr}")
                else:
                    print(f"  비활성화")
            except:
                print("\n[TTL]")
                print("  비활성화")
                
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"\n❌ 테이블 '{table_name}' 존재하지 않음")
            missing_tables.append(table_name)
        except Exception as e:
            print(f"\n❌ 테이블 '{table_name}' 확인 중 에러: {str(e)}")
            missing_tables.append(table_name)
    
    # 최종 요약
    print("\n" + "="*70)
    print("검증 완료")
    print("="*70)
    
    if missing_tables:
        print(f"❌ 누락된 테이블: {', '.join(missing_tables)}")
        print(f"   → python scripts/setup/create_table.py --env {'local' if dynamodb_endpoint else 'aws'} 실행 필요")
        return 1
    else:
        print(f"✅ 모든 테이블({len(TABLE_NAMES)}개) 정상 확인")
        return 0


def main():
    parser = argparse.ArgumentParser(description='DynamoDB 스키마 검증')
    parser.add_argument(
        '--env',
        choices=['local', 'aws'],
        default='local',
        help='환경 선택'
    )
    args = parser.parse_args()
    
    if args.env == 'local':
        endpoint = settings.DYNAMODB_ENDPOINT
    else:
        endpoint = None
    
    return verify_tables(endpoint)


if __name__ == "__main__":
    exit(main())