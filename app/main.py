import os, uuid
from fastapi import FastAPI, Request
from app.api.chat import router as chat_router
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
    if path.startswith("/chat/message"):
        return os.path.join(LOG_DIR, "chat/message")
    return None

@app.middleware("http")
async def request_file_logger_middleware(request: Request, call_next):
    
    body = await request.json()

    thread_id = body.get("thread_id") or str(uuid.uuid4())[:8]

    request.state.thread_id = thread_id
    
    rid = request.headers.get("x-request-id")
    if not rid:
        rid = str(uuid.uuid4())[:8]
        
    log_dir = resolve_request_log_dir(request.url.path)
    if log_dir is not None:
        start_request_file_logging(rid, log_dir, thread_id)

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
app.include_router(chat_router)
