from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
import logging
import re

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 봇 공격 패턴
SCANNER_PATTERNS = [
    r"\.php$",           # PHP 파일
    r"\.env$",           # 환경변수
    r"/actuator/",       # Spring Boot
    r"/admin/",          # 관리자 페이지
    r"/vendor/",         # Composer
    r"/wp-",             # WordPress
    r"/api/\.\./"        # Path traversal
]

def is_scanner_path(path: str) -> bool:
    return any(re.search(pattern, path) for pattern in SCANNER_PATTERNS)

# 미들웨어 등록
@app.middleware("http")
async def detailed_timing(request: Request, call_next):
    start_time = time.time()    
    
    try:
        response = await call_next(request)

    except Exception:
        # 예외 발생 시에도 시간 계산
        total_duration = (time.time() - start_time) * 1000

        if request.url.path != "/health":
            logger.exception(
                f"path={request.url.path} "
                f"total_duration={total_duration:.2f}ms "
                f"method={request.method} "
                f"status=500"
            )
        raise

    # /health 또는 봇 트래픽은 로깅 스팁
    if request.url.path == "/health":
        return response
    
    # 봇 패턴이면 메트릭 제외
    if response.status_code == 404 and is_scanner_path(request.url.path):
        return response
    
    total_duration = (time.time() - start_time) * 1000 #ms
    
    logger.info(
        f"path={request.url.path} "
        f"total_duration={total_duration:.2f}ms "
        f"method={request.method} "
        f"status={response.status_code}"
    )
    
    return response



#router 연결
from app.routers import session_router, chat_router, auth_router
app.include_router(session_router.router) 
app.include_router(chat_router.router) 
app.include_router(auth_router.router) 


#FastAPI 앱 및 템플릿 설정
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(current_dir, "static")),
    name="static",
)

# GET / : login.html 템플릿 렌더링
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    # templates/login.html 파일 렌더링
    return templates.TemplateResponse("login.html", {"request": request})

# GET /main : main.html 템플릿 렌더링
@app.get("/main", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

# GET /health : health check
@app.get("/health")
def health():
    return {"status": "ok"}



