from fastapi import APIRouter, Request
from app.models.schema import AnalyzeRequest
from app.services.vllm_client import analyze_log
from app.utils.network import get_client_addr

router = APIRouter()

@router.post("/analyze")
async def analyze(req: AnalyzeRequest, request: Request):
    client_ip, client_port = get_client_addr(request)
    return await analyze_log(
        message=req.message,
        client_ip=client_ip,
        client_port=client_port,
    )
