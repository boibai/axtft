import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from app.core.config import (
    DAILY_REPORT_SYSTEM_PROMPT_PATH,
)
from app.langgraph.common.utils import truncate_by_tokens
from app.report.utils import (
    load_and_filter_reports,
    build_llm_input,
    load_system_prompt,
    build_user_prompt_daily,
    build_chat_messages,
    save_daily_report,
    get_last_15min_window
)
from app.langgraph.common.llm import call_report_llm
from app.core.logging import get_interval_logger

kst = timezone(timedelta(hours=9))
now = datetime.now(kst)
start_time, end_time = get_last_15min_window(now)

logger = get_interval_logger(start_time, end_time, log_type="daily")

async def run_daily_report() -> dict[str, Any]:
    
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")  # 예: 2026-03-18
    
    reports = load_and_filter_reports(date_str)

    llm_input_text_raw = build_llm_input(reports)
    llm_input_text = truncate_by_tokens(llm_input_text_raw, max_tokens=4096),
    
    system_prompt = load_system_prompt(DAILY_REPORT_SYSTEM_PROMPT_PATH)
    user_prompt = build_user_prompt_daily(
        llm_input=llm_input_text
    )
    
    messages = build_chat_messages(system_prompt, user_prompt)
    
    result = await call_report_llm(messages, type="daily")
    result["report_date"] = date_str
    
    save_path = save_daily_report(result, date_str)
    logger.info(f"[SAVED] {save_path}")

    return result
    
    
def main() -> None:
    result = asyncio.run(run_daily_report())
    logger.info(result)


if __name__ == "__main__":
    main()
    
