from app.langgraph.common.state import ChatState

def extract_answer(state: ChatState) -> ChatState:
    data = state["llm_raw"]
    state["answer"] = data["choices"][0]["message"]["content"]
    return state