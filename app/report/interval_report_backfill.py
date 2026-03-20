import os
import subprocess
import argparse
import time
from datetime import datetime, timedelta, timezone
from app.core.logging import get_interval_backfill_logger

kst = timezone(timedelta(hours=9))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=False, help="YYYY-MM-DD")
    return parser.parse_args()


def iter_windows(start, end, step=10):
    cur = start
    while cur < end:
        nxt = cur + timedelta(minutes=step)
        yield cur, nxt
        cur = nxt
        
def count_json_files(start_dt):
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
    base_dir = (
        f"./data/report/interval/"
        f"{start_time.strftime('%Y')}/"
        f"{start_time.strftime('%m')}/"
        f"{start_time.strftime('%d')}"
    )
    filename = f"{start_time.strftime('%H%M')}_{end_time.strftime('%H%M')}.json"
    return os.path.join(base_dir, filename)


def backfill(start_dt, end_dt ,logger):
    for s, e in iter_windows(start_dt, end_dt):
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
    if now is None:
        now = datetime.now(kst)
        
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start, today_start


def get_date_range(date_str: str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=kst)
    start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt


if __name__ == "__main__":
    args = parse_args()
    
    if args.date:
        start, end = get_date_range(args.date)
    else:
        start, end = get_yesterday_range()

    logger = get_interval_backfill_logger(start)
    logger.info("BACKFILL RANGE: %s ~ %s", start, end)
    backfill(start, end, logger)
    total_files = count_json_files(start)
    logger.info("TOTAL JSON FILE COUNT: %s", total_files)