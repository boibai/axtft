from app.langgraph.chat.state import ChatState
from app.langgraph.chat.tools.tavily import run_tavily

async def run_search(state: ChatState) -> ChatState:
    state["search_result"] = run_tavily(state["search_query"])
    state["searched_for_request"] = state["request_id"]
    return state
