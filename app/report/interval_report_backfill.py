import os
import subprocess
import argparse
import time
from datetime import datetime, timedelta, timezone
from app.core.logging import get_interval_backfill_logger

kst = timezone(timedelta(hours=9))

def parse_args():
    """
    CLI 파라미터
    --date 지정 시 해당 날짜 백필
    미지정 시 어제 기준으로 백필
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=False, help="YYYY-MM-DD")
    return parser.parse_args()


def iter_windows(start, end, step=10):
    """
    start ~ end 구간을 step(분) 단위로 나누는 generator

    예:
    00:00 ~ 01:00 → 10분 단위
    → (00:00~00:10), (00:10~00:20) ...
    """
    cur = start
    while cur < end:
        nxt = cur + timedelta(minutes=step)
        yield cur, nxt
        cur = nxt
        
def count_json_files(start_dt):
    """
    해당 날짜 폴더에 저장된 interval JSON 파일 개수 카운트
    (백필 결과 검증용)
    """
    base_dir = (
        f"./data/report/interval/"
        f"{start_dt.strftime('%Y')}/"
        f"{start_dt.strftime('%m')}/"
        f"{start_dt.strftime('%d')}"
    )
    if not os.path.exists(base_dir):
        return 0

    return len([f for f in os.listdir(base_dir) if f.endswith(".json")])

def get_file_path(start_time, end_time):
    """
    특정 interval 결과 파일 경로 생성

    ex)
    ./data/report/interval/2026/04/23/1200_1210.json
    """
    base_dir = (
        f"./data/report/interval/"
        f"{start_time.strftime('%Y')}/"
        f"{start_time.strftime('%m')}/"
        f"{start_time.strftime('%d')}"
    )
    filename = f"{start_time.strftime('%H%M')}_{end_time.strftime('%H%M')}.json"
    return os.path.join(base_dir, filename)


def backfill(start_dt, end_dt ,logger):
    """
    interval 리포트 백필 실행

    흐름:
    1. 시간 구간을 10분 단위로 나눔
    2. 이미 파일 있으면 skip
    3. 없으면 subprocess로 interval_report 실행
    4. 과부하 방지를 위해 sleep
    """
    for s, e in iter_windows(start_dt, end_dt):
        
        # 시간 제한 (08시 ~ 22시)
        if not (8 <= s.hour < 22):
            #logger.info("SKIP (OUT OF RANGE): %s ~ %s", s, e)
            continue
        
        file_path = get_file_path(s, e)

        if os.path.exists(file_path):
            logger.info("SKIP: %s", file_path)
            continue

        logger.info("RUN : %s ~ %s", s, e)

        subprocess.run([
            "python",
            "-m",
            "app.report.interval_report",
            "--start", s.strftime("%Y-%m-%d %H:%M:%S"),
            "--end", e.strftime("%Y-%m-%d %H:%M:%S"),
        ], check=True)

        time.sleep(300)


def get_yesterday_range(now=None):
    """
    어제 00:00 ~ 오늘 00:00 범위 반환
    (기본 백필 범위)
    """
    if now is None:
        now = datetime.now(kst)
        
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start, today_start


def get_date_range(date_str: str):
    """
    특정 날짜의 00:00 ~ 24:00 범위 반환
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=kst)
    start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt


if __name__ == "__main__":
    args = parse_args()
    
    # 날짜 지정 시 해당 날짜 백필
    if args.date:
        start, end = get_date_range(args.date)
    else:
        # 미지정 시 어제 기준
        start, end = get_yesterday_range()

    # 백필 전용 logger 생성
    logger = get_interval_backfill_logger(start)
    logger.info("BACKFILL RANGE: %s ~ %s", start, end)
    
    # 백필 실행
    backfill(start, end, logger)
    
    # 결과 검증 (생성된 JSON 개수 확인)
    total_files = count_json_files(start)
    logger.info("TOTAL JSON FILE COUNT: %s", total_files)