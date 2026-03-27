from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, StreamingResponse
from app.application.chat_service import handle_chat, clear_chat
from app.langgraph.common.schema import ChatRequest
import json

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/message")
async def chat_message(req: ChatRequest, request: Request):
    thread_id = request.state.thread_id
    return await handle_chat(req, thread_id)
    
@router.delete("/{thread_id}")
def clear_chat_history(thread_id: str):
    clear_chat(thread_id)
    return {"thread_id": thread_id, "cleared": True}

@router.get("/ui")
def chat_ui():
    web_file = Path(__file__).resolve().parent.parent / "web" / "chat.html"
    return FileResponse(web_file)