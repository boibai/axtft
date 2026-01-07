from fastapi import Request
import ipaddress
from app.core.config import ALLOWED_NETWORKS

def get_client_addr(request: Request) -> tuple[str | None, int | None]:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip(), None

    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip(), None

    if request.client:
        return request.client.host, request.client.port

    return None, None

def is_allowed_ip(ip: str) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    return any(ip_obj in net for net in ALLOWED_NETWORKS)
