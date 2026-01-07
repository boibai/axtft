from app.langgraph.analyze.state import AnalyzeState
from app.models.schema import CauseList

def validate_schema(state: AnalyzeState) -> AnalyzeState:
    if state["parsed_json"] is None:
        return state

    try:
        CauseList.model_validate(state["parsed_json"])
        state["error"] = None
    except Exception as e:
        state["error"] = f"Schema validation failed: {e}"

    return state
