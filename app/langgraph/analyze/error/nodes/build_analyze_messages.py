from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_ERROR_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens, count_tokens
from app.core.logging import get_app_logger
logger = get_app_logger()

with open(ANALYZE_ERROR_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()


def build_analyze_messages(state: AnalyzeState) -> AnalyzeState:

    raw_error_log = state["message"].error.stack_trace
    
    error_log = truncate_by_tokens(raw_error_log, max_tokens=2048)
    
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
            "\n\nSYSTEM_METADATA_START\n"
            + "\n".join(metrics_text_lines)
            + "\nSYSTEM_METADATA_END"
        )

    user_prompt = f"""Analyze the following information.
LOG_INPUT_START
{error_log}
LOG_INPUT_END
{metrics_block}
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
    
    logger.info("- USER_PROMPT_TOKEN : %s",count_tokens(user_prompt))
    
    return state
