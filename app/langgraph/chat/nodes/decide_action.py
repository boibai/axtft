from app.langgraph.common.state import ChatState
from app.langgraph.chat.nodes.build_chat_messages import build_decision_messages
from app.langgraph.common.llm import call_decision_llm

async def decide_action(state: ChatState) -> ChatState:
    
    if state.get("search_used_in_turn"):
        state["action"] = "direct"
        return state

    messages = build_decision_messages(state)

    try:
        decision = await call_decision_llm(messages)
        state["action"] = decision.get("action","direct")
        state["search_query"] = decision.get("search_query")
    except Exception as e :
        state["action"] = "direct"

    return state
