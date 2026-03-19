## 임시

from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_ERROR_SYSTEM_PROMPT_PATH
from app.langgraph.common.utils import truncate_by_tokens, count_tokens
from app.core.logging import get_app_logger
logger = get_app_logger()

with open(ANALYZE_ERROR_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

def build_analyze_messages2(state: AnalyzeState) -> AnalyzeState:

    raw_error_log = state["message"].message
    
    error_log = truncate_by_tokens(raw_error_log, max_tokens=4096)

    logger.info("- SYSTEM_PROMPT_TOKEN : %s",count_tokens(system_prompt))

    user_prompt = f"""Analyze the following information.
LOG_INPUT_START
{error_log}
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
    
    logger.info("- USER_PROMPT_TOKEN : %s",count_tokens(user_prompt))
    
    return state
