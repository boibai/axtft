from fastapi import APIRouter

from app.application.chat_service import handle_chat, clear_chat
from app.langgraph.common.schema import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message")
async def chat_message(req: ChatRequest):
    return await handle_chat(req)


@router.delete("/{thread_id}")
def clear_chat_history(thread_id: str):
    clear_chat(thread_id)
    return {"thread_id": thread_id, "cleared": True}