from app.langgraph.common.state import ChatState
from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client
from app.core.config import CHAT_SYSTEM_PROMPT_PATH

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)

with open(CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()


def build_chat_messages(state: ChatState) -> ChatState:
    history = chat_memory.get(state["thread_id"])

    state["messages"] = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": state["request"].message},
    ]

    return state