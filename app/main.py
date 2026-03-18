from fastapi import FastAPI, Request
from app.api.analyze import router as analyze_router
from app.api.report import router as report_router
from app.middleware.ip_whitelist import ip_whitelist_middleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import get_app_logger, start_request_file_logging, stop_request_file_logging

from app.core.config import LOG_DIR
logger = get_app_logger()

app = FastAPI(title="Woongjin Error Log Analyze API")

app.middleware("http")(ip_whitelist_middleware)

@app.middleware("http")
async def request_file_logger_middleware(request: Request, call_next):
    # request_id를 헤더로 받거나, 없으면 생성
    rid = request.headers.get("x-request-id")
    if not rid:
        # uuid를 여기서 만들어도 되고, 기존처럼 service에서 만들어도 됨
        import uuid
        rid = str(uuid.uuid4())[:8]

    start_request_file_logging(rid, LOG_DIR)
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("unhandled exception in request pipeline")
        raise
    finally:
        stop_request_file_logging(rid)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(report_router)
