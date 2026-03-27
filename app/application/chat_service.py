import uuid
from fastapi import HTTPException
from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client
from app.langgraph.common.schema import ChatRequest, ChatResponse
from app.langgraph.chat.graph import chat_graph
from app.core.logging import write_json_data, get_app_logger, get_current_request_id

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)

logger = get_app_logger()

async def handle_chat(req: ChatRequest, thread_id: str) -> ChatResponse:

    logger.info("THREAD_ID : %s", thread_id)
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
    
    logger.info("HISTORY_COUNT : %s",history_count)
    logger.info("MESSAGE : %s",req.message)
    logger.info("ANSWER : %s\n", answer)
    
    if not answer:
        raise HTTPException(status_code=502, detail="chat graph returned empty answer")

    return ChatResponse(
        thread_id=thread_id,
        answer=answer,
        history_count=history_count or 0,
    )


def clear_chat(thread_id: str):
    
    logger.info("The thread ID(%s) session has ended.",thread_id)
    chat_memory.clear(thread_id)
    
