from fastapi import APIRouter, Request
from app.application.analyze_service import handle_error, handle_anomaly, handle_error2
from app.utils.network import get_client_addr
from app.langgraph.common.schema import AnalyzeErrorRequest, AnalyzeAnomalyRequest, AnalyzeErrorMessageRequest
from app.core.time import now_kst_str
from app.core.logging import get_app_logger
logger = get_app_logger()

router = APIRouter(prefix="/analyze")
# ===============================
# 사후 분석
# ===============================
@router.post("/error")
async def analyze_error(req: AnalyzeErrorRequest, request: Request):

    logger.info("%s ANALYZE ERROR API START","=" * 20 )
    
    client_ip, client_port = get_client_addr(request)

    return await handle_error(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )

# ===============================
# 사후 분석
# ===============================
@router.post("/error_message")
async def analyze_error_message(req: AnalyzeErrorMessageRequest, request: Request):

    logger.info("%s ANALYZE ERROR API START","=" * 20 )
    
    client_ip, client_port = get_client_addr(request)

    return await handle_error2(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )


# ===============================
# 사전 분석
# ===============================
@router.post("/anomaly")
async def analyze_anomaly(req: AnalyzeAnomalyRequest, request: Request):

    logger.info("%s ANALYZE ANOMALY API START","=" * 20 )

    client_ip, client_port = get_client_addr(request)

    return await handle_anomaly(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )

