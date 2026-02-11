from fastapi import APIRouter, Request
from app.application.analyze_service import handle_error
from app.utils.network import get_client_addr
from app.langgraph.common.schema import ErrorRequest
from app.core.time import now_kst_str

router = APIRouter()

# ===============================
# 사후 분석
# ===============================
@router.post("/analyze_error")
async def analyze_error(req: ErrorRequest, request: Request):

    print("\n" + "=" * 20 + " ANALYZE ERROR API\n")
    print(f"- time : {now_kst_str('%Y-%m-%d %H:%M:%S')}")

    client_ip, client_port = get_client_addr(request)

    return await handle_error(
        message=req.message,
        client_ip=client_ip,
        client_port=client_port,
    )


# # ===============================
# # 사전 분석
# # ===============================
# @router.post("/analyze_anomaly")
# async def analyze_anomaly(req: AnomalyRequest, request: Request):

#     print("\n" + "=" * 20 + " ANALYZE ANOMALY API\n")
#     print(f"- time : {now_kst_str('%Y-%m-%d %H:%M:%S')}")

#     client_ip, client_port = get_client_addr(request)

#     return await handle_anomaly(
#         signals=req.signals,
#         client_ip=client_ip,
#         client_port=client_port,
#     )

