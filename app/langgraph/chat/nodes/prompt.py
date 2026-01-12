from app.langgraph.chat.state import ChatState
from app.core.config import CHAT_SYSTEM_PROMPT_PATH, TAVILY_CHAT_SYSTEM_PROMPT_PATH
from app.services.memory_store import get_memory
import json

# system prompt 로드
with open(CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_messages_prompt = f.read()

with open(TAVILY_CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_tavily_messages_prompt = f.read()

def build_messages(state: ChatState) -> ChatState:
    history = get_memory(state["thread_id"])

    for m in history:
        print(type(m["content"]), m["role"])

    state["messages"] = (
        [{"role": "system", "content": build_messages_prompt}]
        + history
        + [{"role": "user", "content": state["message"]}]
    )
    return state

def build_search_messages(state: ChatState) -> ChatState:
    history = get_memory(state["thread_id"])

    search_text = json.dumps(
        state["search_result"],
        ensure_ascii=False,
        indent=2,
    )

    print(search_text)
    state["messages"] = (
        [{"role": "system", "content": build_messages_prompt}]
        + history
        + [{"role": "system","content": build_tavily_messages_prompt + search_text}]
        + [{"role": "user", "content": state["message"]}]
    )
    return state