from fastapi import APIRouter, Request
from app.application.analyze_service import handle_analyze_request
from app.utils.network import get_client_addr
from app.langgraph.common.schema import AnalyzeRequest
from app.core.time import now_kst_str

router = APIRouter()


# POST /analyze 엔드포인트 정의
@router.post("/analyze")

async def analyze(req: AnalyzeRequest, request: Request):

    print("\n" + "=" * 20 + " ANALYZE API\n")
    print(f"- time : {now_kst_str("%Y-%m-%d %H:%M:%S")}")

    # 클라이언트의 실제 IP와 포트 추출
    client_ip, client_port = get_client_addr(request)

    # 실제 분석 로직 ( handle_analyze_request )
    return await handle_analyze_request(
        message=req.message,
        client_ip=client_ip,
        client_port=client_port,
    )
