import time
from functools import wraps
from datetime import datetime
from zoneinfo import ZoneInfo

kst = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(tz=kst)

def now_kst_str(fmt: str = "%Y%m%d_%H%M%S") -> str:
    return datetime.now(kst).strftime(fmt)

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            end = time.perf_counter()
            print(f"{func.__name__} took {end - start:.4f}s")
    return wrapper
