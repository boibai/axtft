from datetime import datetime
from zoneinfo import ZoneInfo

kst = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(tz=kst)

def now_kst_str(fmt: str = "%Y%m%d_%H%M%S") -> str:
    return datetime.now(kst).strftime(fmt)
