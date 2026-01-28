from app.langgraph.common.state import AnalyzeState
from app.core.config import ANALYZE_SYSTEM_PROMPT_PATH

with open(ANALYZE_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()


def build_analyze_messages(state: AnalyzeState) -> AnalyzeState:

    state["messages"] = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""Analyze ONLY the log content below.
LOG_INPUT_START
{state["message"]}
LOG_INPUT_END"""
        },
    ]

    return state
