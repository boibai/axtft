from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens, count_tokens, format_logs_as_text
from app.core.logging import get_app_logger
logger = get_app_logger()

with open(ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

def build_analyze_messages(state: AnalyzeState) -> AnalyzeState:
    raw_anomaly_logs = format_logs_as_text(state["message"].logs)
    anomaly_log = truncate_by_tokens(raw_anomaly_logs, max_tokens=4096)
    metadata = state["message"]
    
    logger.info("- SYSTEM_PROMPT_TOKEN : %s",count_tokens(system_prompt))
    
    # 메타데이터 필드 추출
    metric_fields = [
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

    metrics_text_lines = []

    for field in metric_fields:
        value = getattr(metadata, field, None)
        if value is not None:
            metrics_text_lines.append(f"{field}: {value}")

    metrics_block = ""
    if metrics_text_lines:
        metrics_block = (
            "\nSYSTEM_METADATA_START\n\n"
            + "\n".join(metrics_text_lines)
            + "\n\nSYSTEM_METADATA_END\n\n"
        )

    user_prompt = f"""Analyze the following information.
{metrics_block}
LOG_INPUT_START

{anomaly_log}

LOG_INPUT_END
"""
    
    # print(user_prompt)
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
    
    return state
