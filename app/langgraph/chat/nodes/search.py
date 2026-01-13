from app.langgraph.common.state import ChatState
from app.langgraph.chat.tools.tavily import run_tavily, preprocess_tavily_results, stringify_search_results

async def run_search(state: ChatState) -> ChatState:
    print("\n"+"="*20+" SEARCH NODE START\n")
    raw = run_tavily(state["search_query"])
    cleaned = preprocess_tavily_results(raw)
    state["search_result"] = stringify_search_results(cleaned)
    state["searched_for_request"] = state["request_id"]

    return state
