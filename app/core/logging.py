import json
import os
import logging
from typing import Dict, Optional
from contextvars import ContextVar
from datetime import datetime

from app.core.config import DATA_DIR, LOG_DIR

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
log_path_var: ContextVar[Optional[str]] = ContextVar("log_path", default=None)


def write_json_data(filename: str, data: Dict, data_type: str):
    dir_path = os.path.join(DATA_DIR, data_type)
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
    #os.makedirs(log_dir, exist_ok=True)
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

def get_interval_logger(start_time, end_time, log_type):
    logger = logging.getLogger("interval_report")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    date_str = start_time.strftime("%Y-%m-%d")
    
    if log_type == "interval" :
        base_dir = f"./logs/report/interval/{date_str.split("-")[0]}/{date_str.split("-")[1]}/{date_str.split("-")[2]}"
        filename = f"{start_time.strftime('%H%M')}_{end_time.strftime('%H%M')}.txt"
    else :
        base_dir = f"./logs/report/daily/{date_str.split("-")[0]}/{date_str.split("-")[1]}"
        filename = f"{date_str.split("-")[2]}.txt"

    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)
    
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))

    logger.addHandler(fh)
    return logger