# import json, os
# from typing import Dict, Optional
# from app.core.config import LOG_DIR
# import logging
# from contextvars import ContextVar
# from datetime import datetime

# # JSON 로그 파일을 디스크에 저장하는 공통 유틸 함수
# def write_json_log(
#     filename: str,
#     data: Dict,
#     log_type: str,
# ):

#     dir_path = os.path.join(LOG_DIR, log_type)
#     os.makedirs(dir_path, exist_ok=True)
#     path = os.path.join(dir_path, filename)

#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)
        

# # 요청 단위로 request_id / log_file_path를 어디서든 꺼내 쓸 수 있게 함 (async-safe)
# request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
# log_path_var: ContextVar[Optional[str]] = ContextVar("log_path", default=None)


# class RequestContextFilter(logging.Filter):
#     """모든 로그 레코드에 request_id를 자동으로 붙여줌."""
#     def filter(self, record: logging.LogRecord) -> bool:
#         rid = request_id_var.get()
#         record.request_id = rid if rid else "-"
#         return True


# def get_app_logger() -> logging.Logger:
#     """
#     프로젝트 전체에서 공통으로 사용할 로거.
#     - 콘솔 + (요청 시) 파일 핸들러가 붙음
#     """
#     logger = logging.getLogger("axtft")
#     if logger.handlers:
#         return logger  # 이미 초기화됨

#     logger.setLevel(logging.INFO)
#     logger.propagate = False

#     # 콘솔 핸들러(로컬 디버깅/운영 stdout)
#     ch = logging.StreamHandler()
#     ch.setLevel(logging.INFO)

#     fmt = logging.Formatter(
#         "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s"
#     )
#     ch.setFormatter(fmt)

#     logger.addHandler(ch)
#     logger.addFilter(RequestContextFilter())
#     return logger


# def start_request_file_logging(request_id: str, log_dir: str) -> str:
#     """
#     요청 시작 시 호출:
#     - request_id context 설정
#     - 해당 요청 전용 txt 파일 핸들러를 로거에 추가
#     - 로그 파일 경로 반환
#     """
#     os.makedirs(log_dir, exist_ok=True)
#     filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id}.txt"
#     path = os.path.join(log_dir, filename)

#     request_id_var.set(request_id)
#     log_path_var.set(path)

#     logger = get_app_logger()

#     # 파일 핸들러 추가 (요청당 1개)
#     fh = logging.FileHandler(path, encoding="utf-8")
#     fh.setLevel(logging.INFO)
#     fh.setFormatter(logging.Formatter(
#         "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s"
#     ))

#     # 식별용 attribute (요청 끝날 때 제거하려고)
#     fh._axtft_request_id = request_id  # type: ignore[attr-defined]
#     logger.addHandler(fh)

#     logger.info("request logging started: %s", path)
#     return path


# def stop_request_file_logging(request_id: str) -> None:
#     """
#     요청 종료 시 호출:
#     - 해당 request_id용 파일 핸들러 제거/close
#     """
#     logger = get_app_logger()
#     to_remove = []
#     for h in logger.handlers:
#         if getattr(h, "_axtft_request_id", None) == request_id:
#             to_remove.append(h)

#     for h in to_remove:
#         logger.removeHandler(h)
#         try:
#             h.flush()
#             h.close()
#         except Exception:
#             pass
        
# def get_current_request_id() -> Optional[str]:
#     return request_id_var.get()

import json
import os
import logging
from typing import Dict, Optional
from contextvars import ContextVar
from datetime import datetime

from app.core.config import LOG_DIR

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
log_path_var: ContextVar[Optional[str]] = ContextVar("log_path", default=None)


def write_json_log(filename: str, data: Dict, log_type: str):
    dir_path = os.path.join(LOG_DIR, log_type)
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        rid = request_id_var.get()
        record.request_id = rid if rid else "-"
        return True


class RequestFileFilter(logging.Filter):
    def __init__(self, request_id: str):
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "request_id", None) == self.request_id


def get_app_logger() -> logging.Logger:
    logger = logging.getLogger("axtft")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s"
        )
    )

    logger.addHandler(ch)
    logger.addFilter(RequestContextFilter())
    return logger


def start_request_file_logging(request_id: str, log_dir: str) -> str:
    os.makedirs(log_dir, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id}.txt"
    path = os.path.join(log_dir, filename)

    request_id_var.set(request_id)
    log_path_var.set(path)

    logger = get_app_logger()

    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s"
        )
    )
    fh.addFilter(RequestFileFilter(request_id))

    fh._axtft_request_id = request_id  # type: ignore[attr-defined]
    logger.addHandler(fh)

    logger.info("request logging started: %s", path)
    return path


def stop_request_file_logging(request_id: str) -> None:
    logger = get_app_logger()
    to_remove = []

    for h in logger.handlers:
        if getattr(h, "_axtft_request_id", None) == request_id:
            to_remove.append(h)

    for h in to_remove:
        logger.removeHandler(h)
        try:
            h.flush()
            h.close()
        except Exception:
            pass


def get_current_request_id() -> Optional[str]:
    return request_id_var.get()