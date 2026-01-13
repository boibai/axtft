from app.langgraph.common.state import ChatState
from app.langgraph.common.prompt import build_decision_messages
from app.langgraph.common.llm import call_decision_llm

async def decide_action(state: ChatState) -> ChatState:
    # 이미 search를 쓴 turn이면 바로 종료
    if state.get("search_used_in_turn"):
        state["action"] = "direct"
        return state

    messages = build_decision_messages(state)

    try:
        decision = await call_decision_llm(messages)
        state["action"] = decision["action"]
        state["search_query"] = decision.get("search_query")
    except Exception as e :
        state["action"] = "direct"

    return state
