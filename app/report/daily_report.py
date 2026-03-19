import asyncio, json
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

async def run_with_retry(max_retries: int = 3, delay_sec: int = 5):
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("RUN ATTEMPT %d/%d", attempt, max_retries)
            result = await run_daily_report()
            return result

        except Exception as e:
            logger.exception("RUN FAILED (attempt %d/%d)", attempt, max_retries)

            if attempt == max_retries:
                logger.error("ALL RETRIES FAILED")
                raise

            logger.info("RETRY AFTER %s sec...", delay_sec)
            await asyncio.sleep(delay_sec)
            
async def run_daily_report() -> dict[str, Any]:
    
    logger.info("%s RUN DAILY REPORT","=" * 20 )
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")  # 예: 2026-03-18
    
    logger.info("- TARGET DATE : %s", date_str)
    reports = load_and_filter_reports(date_str)

    llm_input_text_raw = build_llm_input(reports)
    llm_input_text = truncate_by_tokens(llm_input_text_raw, max_tokens=4096),
    
    logger.info("%s INPUT INTERVAL REPORTS","=" * 20 )
    logger.info("\n%s",llm_input_text[0])
    system_prompt = load_system_prompt(DAILY_REPORT_SYSTEM_PROMPT_PATH)
    user_prompt = build_user_prompt_daily(
        llm_input=llm_input_text
    )
    
    messages = build_chat_messages(system_prompt, user_prompt)
    
    result, metadata = await call_report_llm(messages, type="daily")
    result["report_date"] = date_str
    
    logger.info("%s META DATA","=" * 20 )
    logger.info(json.dumps(metadata, ensure_ascii=False, indent=2))

    logger.info("%s LLM RESULT","=" * 20 )
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    
    save_path = save_daily_report(result, date_str)
    logger.info(f"{"=" * 20 } SAVED DATA : {save_path}")

    return result
    
def main() -> None:
    try:
        result = asyncio.run(run_with_retry())
        print(result)
    except Exception as e:
        logger.error("FINAL FAILURE: %s", str(e))
        
if __name__ == "__main__":
    main()
    
