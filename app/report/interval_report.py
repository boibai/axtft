import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from dateutil.parser import parse

from app.langgraph.common.llm import call_report_llm
from app.report.utils import (
    format_logs_for_llm,
    get_last_15min_window,
    parse_log_message,
    fetch_logs,
    build_log_llm_input,
    build_metric_queries,
    fetch_metric_time_map,
    aggregate_metrics,
    get_valid_metric_names,
    build_metric_llm_input,
    load_system_prompt,
    build_user_prompt,
    build_chat_messages,
    save_interval_report
)

from app.core.config import (
    INTERVAL_REPORT_SYSTEM_PROMPT_PATH,
)

kst = timezone(timedelta(hours=9))

async def run_interval_report() -> dict[str, Any]:
    now = datetime.now(kst)
    start_time, end_time = get_last_15min_window(now)

    print(start_time)
    print(end_time)

    logs = fetch_logs(now=now, start_time=start_time, end_time=end_time)
    log_llm_input = build_log_llm_input(logs)

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
    user_prompt = build_user_prompt(
        metric_llm_input=metric_llm_input,
        log_llm_input=log_llm_input,
    )
    messages = build_chat_messages(system_prompt, user_prompt)

    result = await call_report_llm(messages)
    result["timeWindow"] = {
        "start": start_time.strftime("%H:%M:%S"),
        "end": end_time.strftime("%H:%M:%S"),
    }
    save_path = save_interval_report(result, start_time, end_time)
    print(f"[SAVED] {save_path}")

    return result


def main() -> None:
    result = asyncio.run(run_interval_report())
    print(result)


if __name__ == "__main__":
    main()