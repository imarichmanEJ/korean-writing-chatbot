from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    - ECS Task Definition Health Check에서 사용
    - ALB Target Group Health Check에서도 사용 가능
    """
    try:
        # 1. 기본 응답
        health_status = {
            "status": "healthy",
            "service": "korean-writing-chatbot",
            "version": "1.0.0"
        }
        
        # 2. DynamoDB 연결 체크 (선택사항)
        # try:
        #     dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
        #     table = dynamodb.Table('Users')
        #     table.table_status  # 테이블 상태 확인
        #     health_status["dynamodb"] = "connected"
        # except Exception as e:
        #     health_status["dynamodb"] = "disconnected"
        #     health_status["status"] = "unhealthy"
        
        # 3. OpenAI API 키 존재 체크 (선택사항)
        # import os
        # if os.getenv("OPENAI_API_KEY"):
        #     health_status["openai_key"] = "configured"
        # else:
        #     health_status["openai_key"] = "missing"
        #     health_status["status"] = "unhealthy"
        
        if health_status["status"] == "healthy":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=health_status
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_status
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )