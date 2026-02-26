from typing import Iterable
from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens, count_tokens, format_logs_as_text
from app.core.logging import get_app_logger

logger = get_app_logger()

with open(ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

METRIC_FIELDS = [
    "timestamp",
    "http_error_rate",
    "latency_p95",
    "latency_p99",
    "service_status",
    "cpu_usage",
    "memory_usage",
    "throughput",
    "db_connection_pool",
    "disk_usage",
]

def build_metrics_block_all(metrics: Iterable) -> str:
    metrics = list(metrics)
    if not metrics:
        return ""

    # 시간 순 정렬
    metrics.sort(key=lambda m: m.timestamp)

    lines = []
    for m in metrics:
        # 한 타임포인트를 한 줄로 (가독성 좋게)
        parts = []
        for field in METRIC_FIELDS:
            value = getattr(m, field, None)
            if value is None:
                continue
            if field == "timestamp":
                value = value.isoformat()
            parts.append(f"{field}: {value}")

        if parts:
            lines.append(" | ".join(parts))

    if not lines:
        return ""

    return (
        "\nSYSTEM_METADATA_START\n\n"
        + "\n".join(lines)
        + "\n\nSYSTEM_METADATA_END\n\n"
    )
    
def build_analyze_messages(state: AnalyzeState) -> AnalyzeState:
    raw_anomaly_logs = format_logs_as_text(state["message"].logs)
    anomaly_log = truncate_by_tokens(raw_anomaly_logs, max_tokens=4096)
    metadata = state["message"].metrics
    logger.info("- SYSTEM_PROMPT_TOKEN : %s",count_tokens(system_prompt))
    
    metrics_block = build_metrics_block_all(metadata)
    user_prompt = f"""Analyze the following information.
{metrics_block}
LOG_INPUT_START

{anomaly_log}

LOG_INPUT_END
"""
    
    state["messages"] = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        },
    ]
    
    logger.info("- USER_PROMPT_TOKEN  : %s",count_tokens(user_prompt))
    print(user_prompt)
    return state
