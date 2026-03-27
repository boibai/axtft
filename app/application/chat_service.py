import uuid

from fastapi import HTTPException

from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client
from app.langgraph.common.schema import ChatRequest, ChatResponse
from app.langgraph.chat.graph import chat_graph

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)


async def handle_chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or str(uuid.uuid4())[:8]

    state = {
        "thread_id": thread_id,
        "request": req,
    }

    try:
        result = await chat_graph.ainvoke(state)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"chat graph failed: {exc}") from exc

    answer = result.get("answer")
    history_count = result.get("history_count")

    if not answer:
        raise HTTPException(status_code=502, detail="chat graph returned empty answer")

    return ChatResponse(
        thread_id=thread_id,
        answer=answer,
        history_count=history_count or 0,
    )


def clear_chat(thread_id: str):
    chat_memory.clear(thread_id)