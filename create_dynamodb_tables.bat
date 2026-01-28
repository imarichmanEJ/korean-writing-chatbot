@echo off
setlocal enabledelayedexpansion

set REGION=ap-northeast-2

echo DynamoDB 테이블 생성 시작 (ON_DEMAND 모드)...
echo.

REM ========================================
REM 1. Users 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Users ^
    --attribute-definitions ^
        AttributeName=user_id,AttributeType=S ^
        AttributeName=email,AttributeType=S ^
    --key-schema ^
        AttributeName=user_id,KeyType=HASH ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"EmailIndex\",\"KeySchema\": [{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Users 테이블 생성 완료
echo.

REM ========================================
REM 2. Sessions 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Sessions ^
    --attribute-definitions ^
        AttributeName=user_id,AttributeType=S ^
        AttributeName=session_id,AttributeType=S ^
        AttributeName=updated_at,AttributeType=S ^
    --key-schema ^
        AttributeName=user_id,KeyType=HASH ^
        AttributeName=session_id,KeyType=RANGE ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"UserUpdatedAtIndex\",\"KeySchema\": [{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"updated_at\",\"KeyType\":\"RANGE\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Sessions 테이블 생성 완료
echo.

REM ========================================
REM 3. Messages 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Messages ^
    --attribute-definitions ^
        AttributeName=session_id,AttributeType=S ^
        AttributeName=timestamp,AttributeType=S ^
    --key-schema ^
        AttributeName=session_id,KeyType=HASH ^
        AttributeName=timestamp,KeyType=RANGE ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Messages 테이블 생성 완료
echo.

REM ========================================
REM 4. Tasks 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Tasks ^
    --attribute-definitions ^
        AttributeName=user_id,AttributeType=S ^
        AttributeName=created_at,AttributeType=S ^
        AttributeName=session_id,AttributeType=S ^
        AttributeName=task_id,AttributeType=S ^
    --key-schema ^
        AttributeName=user_id,KeyType=HASH ^
        AttributeName=created_at,KeyType=RANGE ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"SessionTasksIndex\",\"KeySchema\": [{\"AttributeName\":\"session_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}},{\"IndexName\": \"TaskIdIndex\",\"KeySchema\": [{\"AttributeName\":\"task_id\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Tasks 테이블 생성 완료
echo.

REM ========================================
REM 5. Questions 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Questions ^
    --attribute-definitions ^
        AttributeName=session_id,AttributeType=S ^
        AttributeName=created_at,AttributeType=S ^
        AttributeName=question_id,AttributeType=S ^
    --key-schema ^
        AttributeName=session_id,KeyType=HASH ^
        AttributeName=created_at,KeyType=RANGE ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"QuestionIdIndex\",\"KeySchema\": [{\"AttributeName\":\"question_id\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Questions 테이블 생성 완료
echo.

REM ========================================
REM 6. Submissions 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Submissions ^
    --attribute-definitions ^
        AttributeName=user_id,AttributeType=S ^
        AttributeName=submitted_at,AttributeType=S ^
        AttributeName=submission_id,AttributeType=S ^
        AttributeName=question_id,AttributeType=S ^
    --key-schema ^
        AttributeName=user_id,KeyType=HASH ^
        AttributeName=submitted_at,KeyType=RANGE ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"SubmissionIdIndex\",\"KeySchema\": [{\"AttributeName\":\"submission_id\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}},{\"IndexName\": \"QuestionSubmissionsIndex\",\"KeySchema\": [{\"AttributeName\":\"question_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"submitted_at\",\"KeyType\":\"RANGE\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Submissions 테이블 생성 완료
echo.

REM ========================================
REM 7. Evaluations 테이블
REM ========================================
aws dynamodb create-table ^
    --table-name Evaluations ^
    --attribute-definitions ^
        AttributeName=user_id,AttributeType=S ^
        AttributeName=created_at,AttributeType=S ^
        AttributeName=evaluation_id,AttributeType=S ^
        AttributeName=submission_id,AttributeType=S ^
        AttributeName=session_id,AttributeType=S ^
    --key-schema ^
        AttributeName=user_id,KeyType=HASH ^
        AttributeName=created_at,KeyType=RANGE ^
    --global-secondary-indexes ^
        "[{\"IndexName\": \"EvaluationIdIndex\",\"KeySchema\": [{\"AttributeName\":\"evaluation_id\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}},{\"IndexName\": \"SubmissionEvaluationIndex\",\"KeySchema\": [{\"AttributeName\":\"submission_id\",\"KeyType\":\"HASH\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}},{\"IndexName\": \"SessionEvaluationIndex\",\"KeySchema\": [{\"AttributeName\":\"session_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}],\"Projection\": {\"ProjectionType\":\"ALL\"}}]" ^
    --billing-mode ON_DEMAND ^
    --region %REGION%

echo [OK] Evaluations 테이블 생성 완료
echo.

echo ===================================
echo [완료] 7개 DynamoDB 테이블 생성 완료!
echo ===================================
echo.

REM 테이블 목록 확인
aws dynamodb list-tables --region %REGION%

pause