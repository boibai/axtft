import asyncio, json, argparse
from datetime import datetime, timezone, timedelta
from typing import Any
from app.langgraph.common.llm import call_report_llm
from app.langgraph.common.utils import truncate_by_tokens
from app.report.utils import (
    get_last_15min_window,
    fetch_logs,
    build_log_llm_input,
    build_metric_queries,
    fetch_metric_time_map,
    aggregate_metrics,
    get_valid_metric_names,
    build_metric_llm_input,
    load_system_prompt,
    build_user_prompt_interval,
    build_chat_messages,
    save_interval_report
)

from app.core.config import (
    INTERVAL_REPORT_SYSTEM_PROMPT_PATH,
)
from app.core.logging import get_interval_logger

kst = timezone(timedelta(hours=9))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, required=False)
    parser.add_argument("--end", type=str, required=False)
    return parser.parse_args()

async def run_with_retry(start_time, end_time, logger, max_retries: int = 3, delay_sec: int = 60):
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("RUN ATTEMPT %d/%d", attempt, max_retries)
            result = await run_interval_report(start_time, end_time, logger)
            return result

        except Exception:
            logger.exception("RUN FAILED (attempt %d/%d)", attempt, max_retries)

            if attempt == max_retries:
                logger.error("ALL RETRIES FAILED")
                raise

            logger.info("RETRY AFTER %s sec...", delay_sec)
            await asyncio.sleep(delay_sec)
            
async def run_interval_report(start_time, end_time, logger) -> dict[str, Any]:

    now = end_time 
    
    logger.info("%s RUN INTERVAL REPORT","=" * 20 )
    logger.info("- START TIME : %s", start_time)
    logger.info("- END TIME : %s", end_time)
    
    try :
        logs = fetch_logs(now=now, start_time=start_time, end_time=end_time)
    except Exception as e :
        logger.error(e)
        logs = ""
    
    log_llm_input = truncate_by_tokens(build_log_llm_input(logs), max_tokens=4096)
    
    queries = build_metric_queries()
    metric_names = list(queries.keys())

    time_map = fetch_metric_time_map(
        queries=queries,
        start_time=start_time,
        end_time=end_time,
        step="1s",
    )

    aggregated_map = aggregate_metrics(
        time_map=time_map,
        metric_names=metric_names,
        bucket_seconds=10,
    )

    valid_metric_names = get_valid_metric_names(
        aggregated_map=aggregated_map,
        metric_names=metric_names,
        null_ratio_threshold=0.8,
    )

    metric_llm_input = build_metric_llm_input(
        aggregated_map=aggregated_map,
        valid_metric_names=valid_metric_names,
        min_non_null_ratio=0.7,
    )

    system_prompt = load_system_prompt(INTERVAL_REPORT_SYSTEM_PROMPT_PATH)
    
    logger.info("%s LOG INPUT","=" * 20 )
    logger.info(log_llm_input)
    
    logger.info("%s METRIC INPUT","=" * 20 )
    logger.info(metric_llm_input) 
    user_prompt = build_user_prompt_interval(
        metric_llm_input=metric_llm_input,
        log_llm_input=log_llm_input
    )
    
    messages = build_chat_messages(system_prompt, user_prompt)

    result, metadata = await call_report_llm(messages, type="interval")
    result["timeWindow"] = {
        "start": start_time.strftime("%H:%M:%S"),
        "end": end_time.strftime("%H:%M:%S"),
    }
    
    logger.info("%s META DATA","=" * 20 )
    logger.info(json.dumps(metadata, ensure_ascii=False, indent=2))

    logger.info("%s LLM RESULT","=" * 20 )
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    
    save_path = save_interval_report(result, start_time, end_time)
    logger.info(f"{"=" * 20 } SAVED DATA : {save_path}")

    return result


def main() -> None:
    args = parse_args()

    if args.start and args.end:

        start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=kst)
        end_time = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S").replace(tzinfo=kst)
    else:
        now = datetime.now(kst)
        start_time, end_time = get_last_15min_window(now)

    logger = get_interval_logger(start_time, end_time)

    try:
        result = asyncio.run(run_with_retry(start_time, end_time, logger))
        print(result)
    except Exception as e:
        logger.error("FINAL FAILURE: %s", str(e))


if __name__ == "__main__":
    main()