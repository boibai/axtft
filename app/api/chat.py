from fastapi import APIRouter, Request
from pydantic import BaseModel
import uuid

from app.services.chat_client import chat_log
from app.utils.network import get_client_addr

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    client_ip, client_port = get_client_addr(request)
    thread_id = req.thread_id or str(uuid.uuid4())

    return await chat_log(
        message=req.message,
        thread_id=thread_id,
        client_ip=client_ip,
        client_port=client_port,
    )
