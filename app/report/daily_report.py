import asyncio
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import DAILY_REPORT_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens
from app.report.utils import (
    load_and_filter_reports,
    build_llm_input,
    load_system_prompt,
    build_user_prompt_daily,
    build_chat_messages,
    save_daily_report,
    get_yesterday,
)
from app.langgraph.common.llm import call_report_llm
from app.core.logging import get_daily_logger

kst = timezone(timedelta(hours=9))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=False, help="YYYY-MM-DD")
    return parser.parse_args()


def get_target_date(date_str: str | None) -> datetime:
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=kst)

    now = datetime.now(kst)
    return get_yesterday(now)


async def run_with_retry(target_time: datetime, logger, max_retries: int = 3, delay_sec: int = 60):
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("RUN ATTEMPT %d/%d", attempt, max_retries)
            result = await run_daily_report(target_time, logger)
            return result

        except Exception:
            logger.exception("RUN FAILED (attempt %d/%d)", attempt, max_retries)

            if attempt == max_retries:
                logger.error("ALL RETRIES FAILED")
                raise

            logger.info("RETRY AFTER %s sec...", delay_sec)
            await asyncio.sleep(delay_sec)


async def run_daily_report(target_time: datetime, logger) -> dict[str, Any]:
    logger.info("%s RUN DAILY REPORT", "=" * 20)

    date_str = target_time.strftime("%Y-%m-%d")
    logger.info("- TARGET DATE : %s", date_str)

    reports = load_and_filter_reports(date_str)

    llm_input_text_raw = build_llm_input(reports)
    llm_input_text = truncate_by_tokens(llm_input_text_raw, max_tokens=8192)

    logger.info("%s INPUT INTERVAL REPORTS", "=" * 20)
    logger.info("\n%s", llm_input_text)

    system_prompt = load_system_prompt(DAILY_REPORT_SYSTEM_PROMPT_PATH)
    user_prompt = build_user_prompt_daily(
        llm_input=llm_input_text
    )

    messages = build_chat_messages(system_prompt, user_prompt)

    result, metadata = await call_report_llm(messages, type="daily")
    result["report_date"] = date_str

    logger.info("%s META DATA", "=" * 20)
    logger.info(json.dumps(metadata, ensure_ascii=False, indent=2))

    logger.info("%s LLM RESULT", "=" * 20)
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))

    save_path = save_daily_report(result, date_str)
    logger.info("%s SAVED DATA : %s", "=" * 20, save_path)

    return result


def main() -> None:
    args = parse_args()

    try:
        target_time = get_target_date(args.date)
        logger = get_daily_logger(target_time)

        result = asyncio.run(run_with_retry(target_time, logger))
        print(result)

    except Exception as e:
        print(f"FINAL FAILURE: {e}")
        raise


if __name__ == "__main__":
    main()