from fastapi import APIRouter, Request
import uuid

from app.application.chat_service import handle_chat_request
from app.utils.network import get_client_addr
from app.langgraph.common.schema import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    client_ip, client_port = get_client_addr(request)
    thread_id = req.thread_id or str(uuid.uuid4())

    return await handle_chat_request(
        message=req.message,
        thread_id=thread_id,
        client_ip=client_ip,
        client_port=client_port,
    )
