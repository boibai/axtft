import json, os, re
from fastapi import APIRouter, Request, HTTPException
from app.core.config import DATA_DIR
from app.application.analyze_service import handle_error, handle_anomaly, handle_error2
from app.utils.network import get_client_addr
from app.langgraph.common.schema import AnalyzeErrorRequest, AnalyzeAnomalyRequest, AnalyzeErrorMessageRequest, ListRequest, FileRequest
from app.core.logging import get_app_logger
logger = get_app_logger()

router = APIRouter(prefix="/analyze")

def get_anlayze_base_dir(type:str) -> str:
    return os.path.join(DATA_DIR, "analyze", type)


@router.post("/error")
async def analyze_error(req: AnalyzeErrorRequest, request: Request):

    logger.info("%s ANALYZE ERROR API START","=" * 20 )
    
    client_ip, client_port = get_client_addr(request)

    return await handle_error(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )

## 임시
@router.post("/error_message")
async def analyze_error_message(req: AnalyzeErrorMessageRequest, request: Request):

    logger.info("%s ANALYZE ERROR API START","=" * 20 )
    
    client_ip, client_port = get_client_addr(request)

    return await handle_error2(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )


@router.post("/anomaly")
async def analyze_anomaly(req: AnalyzeAnomalyRequest, request: Request):

    logger.info("%s ANALYZE ANOMALY API START","=" * 20 )

    client_ip, client_port = get_client_addr(request)

    return await handle_anomaly(
        message=req,
        client_ip=client_ip,
        client_port=client_port,
    )


@router.post("/anomaly/list")
def list_analyze_anomaly(req: ListRequest):
    date = req.date
    base_dir = get_anlayze_base_dir(type="anomaly")
    
    date_dir = os.path.join(base_dir,date.split("-")[0],date.split("-")[1],date.split("-")[2])

    if not os.path.isdir(date_dir):
        raise HTTPException(status_code=404, detail=f"No anomaly file directory for date={req.date}")

    files = [
        f.split(".")[0] for f in os.listdir(date_dir)
        if f.endswith(".json") and os.path.isfile(os.path.join(date_dir, f))
    ]
    files.sort()

    return {
        "date": req.date,
        "count": len(files),
        "files": files,
    }


@router.post("/anomaly/file")
def get_analyze_anomaly_file(req: FileRequest):
    pattern = r"^\d{8}_\d{6}_[a-z0-9]{8}$"
    print(req.filename)
    if not re.match(pattern, req.filename):
        raise HTTPException(
            status_code=400,
            detail="filename must match pattern 00000000_000000_########"
        )
    date = req.date
    base_dir = get_anlayze_base_dir(type="anomaly")
    file_path = os.path.join(base_dir, date.split("-")[0],date.split("-")[1],date.split("-")[2], req.filename+".json")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="anomaly file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.post("/error/list")
def list_analyze_error(req: ListRequest):
    date = req.date
    base_dir = get_anlayze_base_dir(type="error")
    
    date_dir = os.path.join(base_dir,date.split("-")[0],date.split("-")[1],date.split("-")[2])

    if not os.path.isdir(date_dir):
        raise HTTPException(status_code=404, detail=f"No error file directory for date={req.date}")

    files = [
        f.split(".")[0] for f in os.listdir(date_dir)
        if f.endswith(".json") and os.path.isfile(os.path.join(date_dir, f))
    ]
    files.sort()

    return {
        "date": req.date,
        "count": len(files),
        "files": files,
    }


@router.post("/error/file")
def get_analyze_error_file(req: FileRequest):
    pattern = r"^\d{8}_\d{6}_[a-z0-9]{8}$"
    print(req.filename)
    if not re.match(pattern, req.filename):
        raise HTTPException(
            status_code=400,
            detail="filename must match pattern 00000000_000000_########"
        )
    date = req.date
    base_dir = get_anlayze_base_dir(type="error")
    file_path = os.path.join(base_dir, date.split("-")[0],date.split("-")[1],date.split("-")[2], req.filename+".json")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="error file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data