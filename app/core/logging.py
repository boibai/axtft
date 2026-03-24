import json
import os
import logging
from typing import Dict, Optional
from contextvars import ContextVar
from datetime import datetime, timezone, timedelta
from app.core.config import DATA_DIR, LOG_DIR

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
log_path_var: ContextVar[Optional[str]] = ContextVar("log_path", default=None)

def write_json_data(filename: str, data: Dict, data_type: str):

    date_str = filename.split("_")[0] 

    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:8]

    dir_path = os.path.join(DATA_DIR, data_type, year, month, day)
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

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request_id}.txt"

    date_str = filename.split("_")[0]
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:8]

    dir_path = os.path.join(log_dir, year, month, day)
    os.makedirs(dir_path, exist_ok=True)

    path = os.path.join(dir_path, filename)

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

    fh._axtft_request_id = request_id
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

def get_interval_logger(start_time, end_time):

    logger = logging.getLogger("interval_report")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    date_str = start_time.strftime("%Y-%m-%d")

    base_dir = f"./logs/report/interval/{date_str.split("-")[0]}/{date_str.split("-")[1]}/{date_str.split("-")[2]}"
    filename = f"{start_time.strftime('%H%M')}_{end_time.strftime('%H%M')}.txt"

    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)
    
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))

    logger.addHandler(fh)
    return logger


def get_daily_logger(target_date):

    logger = logging.getLogger("daily_report")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    yesterday_str = target_date.strftime("%Y-%m-%d")
    
    base_dir = f"./logs/report/daily/{yesterday_str.split("-")[0]}/{yesterday_str.split("-")[1]}"
    filename = f"{yesterday_str.split("-")[2]}.txt"

    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)
    
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))

    logger.addHandler(fh)
    return logger

def get_interval_backfill_logger(start_time):

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    logger_name = f"interval_backfill_{now.strftime('%Y%m%d_%H%M')}"
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    date_str = start_time.strftime("%Y-%m-%d")

    base_dir = f"./logs/report/interval_backfill/{date_str.split("-")[0]}/{date_str.split("-")[1]}/{date_str.split("-")[2]}"
    filename = f"{logger_name}.txt"

    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)
    
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s"
    ))

    logger.addHandler(fh)
    return logger