from fastapi import APIRouter, Request
from app.application.analyze_service import handle_analyze_request
from app.utils.network import get_client_addr
from app.langgraph.common.schema import AnalyzeRequest

router = APIRouter()

@router.post("/analyze")
async def analyze(req: AnalyzeRequest, request: Request):
    client_ip, client_port = get_client_addr(request)
    return await handle_analyze_request(
        message=req.message,
        client_ip=client_ip,
        client_port=client_port,
    )
