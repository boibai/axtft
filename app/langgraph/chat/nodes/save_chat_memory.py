from app.langgraph.common.state import ChatState
from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)

def save_chat_memory(state: ChatState) -> ChatState:
    chat_memory.append_turn(
        thread_id=state["thread_id"],
        user_message=state["request"].message,
        assistant_message=state["answer"],
    )

    state["history_count"] = len(chat_memory.get(state["thread_id"]))
    return state