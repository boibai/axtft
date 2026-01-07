from datetime import datetime
from zoneinfo import ZoneInfo

# 한국시간으로 설정
kst = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(tz=kst)

def now_kst_str(fmt: str = "%Y%m%d_%H%M%S") -> str:
    return datetime.now(kst).strftime(fmt)
