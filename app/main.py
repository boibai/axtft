import os
from fastapi import FastAPI, Request
from app.api.analyze import router as analyze_router
from app.api.report import router as report_router
from app.middleware.ip_whitelist import ip_whitelist_middleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import start_request_file_logging, stop_request_file_logging

from app.core.config import LOG_DIR

app = FastAPI(title="Woongjin Error Log Analyze API")

app.middleware("http")(ip_whitelist_middleware)

def resolve_request_log_dir(path: str) -> str:
    if path.startswith("/analyze/error_message"):
        return os.path.join(LOG_DIR, "analyze/error")
    if path.startswith("/analyze/anomaly"):
        return os.path.join(LOG_DIR, "analyze/anomaly")
    return None

@app.middleware("http")
async def request_file_logger_middleware(request: Request, call_next):
    # request_id를 헤더로 받거나, 없으면 생성
    rid = request.headers.get("x-request-id")
    if not rid:
        # uuid를 여기서 만들어도 되고, 기존처럼 service에서 만들어도 됨
        import uuid
        rid = str(uuid.uuid4())[:8]
        
    log_dir = resolve_request_log_dir(request.url.path)
    if log_dir is not None:
        start_request_file_logging(rid, log_dir)

    try:
        response = await call_next(request)
        return response
    finally:
        if log_dir is not None:
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
