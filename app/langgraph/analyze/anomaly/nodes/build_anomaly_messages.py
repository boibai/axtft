from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens, count_tokens, format_logs_as_table, build_metrics_block_table
from app.core.logging import get_app_logger

logger = get_app_logger()

with open(ANALYZE_ANOMALY_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

def build_analyze_messages(state: AnalyzeState) -> AnalyzeState:
    raw_anomaly_logs = format_logs_as_table(state["message"].logs)
    anomaly_log = truncate_by_tokens(raw_anomaly_logs, max_tokens=8192)
    metadata = state["message"].metrics
    
    logger.info("- SYSTEM_PROMPT_TOKEN : %s",count_tokens(system_prompt))
    logger.info("- SYSTEM_PROMPT : \n%s",system_prompt)
    metrics_block = build_metrics_block_table(metadata)
    
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
    logger.info("- USER_PROMPT : \n%s",user_prompt)
    
    return state
