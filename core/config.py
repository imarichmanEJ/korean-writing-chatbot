import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIAL_DIR = BASE_DIR / "credential"
ENV_PATH = CREDENTIAL_DIR / ".env"

# 환경변수 로드
load_dotenv(ENV_PATH)

class Settings:
    """애플리케이션 설정"""
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")  # local, dev, prod
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    FT_EVAL_MODEL_ID: str = os.getenv("FT_EVAL_MODEL_ID", "")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-2")
    LLM_MODEL: str = "gpt-4o"

    DYNAMODB_ENDPOINT: Optional[str] = os.getenv("DYNAMODB_ENDPOINT", None)
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    BASE_DIR: Path = BASE_DIR
    CREDENTIAL_DIR: Path = CREDENTIAL_DIR

settings = Settings()

OPENAI_API_KEY = settings.OPENAI_API_KEY
LANGSMITH_API_KEY = settings.LANGSMITH_API_KEY
FT_EVAL_MODEL_ID = settings.FT_EVAL_MODEL_ID
SECRET_KEY = settings.SECRET_KEY
LLM_MODEL = settings.LLM_MODEL