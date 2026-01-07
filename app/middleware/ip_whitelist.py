from fastapi import Request
from fastapi.responses import JSONResponse

from app.utils.network import get_client_addr, is_allowed_ip
from app.core.config import ENABLE_IP_WHITELIST

async def ip_whitelist_middleware(request: Request, call_next):
    if not ENABLE_IP_WHITELIST:
        return await call_next(request)

    client_ip, client_port = get_client_addr(request)

    if not client_ip or not is_allowed_ip(client_ip):
        return JSONResponse(
            status_code=403,
            content={
                "detail": "Access denied",
                "client_ip": client_ip,
                "client_port": client_port,
            },
        )

    return await call_next(request)
