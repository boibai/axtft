import json
from app.langgraph.common.state import AnalyzeErrorState

def parse_json(state: AnalyzeErrorState) -> AnalyzeErrorState:

    try:
        state["parsed_json"] = json.loads(state["llm_content"])
        state["error"] = None

    except Exception as e:

        state["parsed_json"] = None
        state["error"] = f"JSON parse failed: {e}"

    return state
