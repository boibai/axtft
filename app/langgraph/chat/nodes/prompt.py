from app.langgraph.chat.state import ChatState
from app.core.config import CHAT_SYSTEM_PROMPT_PATH
from app.services.memory_store import get_memory

# system prompt 로드
with open(CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

def build_messages(state: ChatState) -> ChatState:
    history = get_memory(state["thread_id"])

    state["messages"] = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": state["message"]}]
    )
    return state

