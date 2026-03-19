import json
import os, re
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from app.core.config import LOG_DIR
from app.report.schema import IntervalReportRequest, IntervalReportFileRequest

router = APIRouter(prefix="/report", tags=["report"])

def get_interval_report_base_dir(type:str) -> str:
    return os.path.join(LOG_DIR, "report", type)


@router.post("/interval")
def list_interval_reports(req: IntervalReportRequest):
    date = req.date
    base_dir = get_interval_report_base_dir(type="interval")
    
    date_dir = os.path.join(base_dir,date.split("-")[0],date.split("-")[1],date.split("-")[2])

    if not os.path.isdir(date_dir):
        raise HTTPException(status_code=404, detail=f"No interval report directory for date={req.date}")

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


@router.post("/interval/file")
def get_interval_report(req: IntervalReportFileRequest):
    pattern = r"^\d{4}_\d{4}$"
    print(req.filename)
    if not re.match(pattern, req.filename):
        raise HTTPException(
            status_code=400,
            detail="filename must match pattern 0000_0000"
        )
    date = req.date
    base_dir = get_interval_report_base_dir(type="interval")
    file_path = os.path.join(base_dir, date.split("-")[0],date.split("-")[1],date.split("-")[2], req.filename+".json")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="report file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.post("/daily")
def list_daily_reports(req: IntervalReportRequest):
    date = req.date
    base_dir = get_interval_report_base_dir(type="daily")
    date_dir = os.path.join(base_dir,date.split("-")[0],date.split("-")[1])
    if not os.path.isdir(date_dir):
        raise HTTPException(status_code=404, detail=f"No interval report directory for date={req.date}")

    files = [
        f.split(".")[0] for f in os.listdir(date_dir)
        if f.endswith(".json") and os.path.isfile(os.path.join(date_dir, f))
    ]
    files.sort()

    return {
        "date": f"{date.split("-")[0]}-{date.split("-")[1]}",
        "count": len(files),
        "files": files,
    }


@router.post("/daily/file")
def get_daily_report(req: IntervalReportRequest):
    
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, req.date):
        raise HTTPException(
            status_code=400,
            detail="date must match pattern YYYY-MM-DD"
    )
    date = req.date
    base_dir = get_interval_report_base_dir(type="daily")
    file_path = os.path.join(base_dir, date.split("-")[0],date.split("-")[1], date.split("-")[2]+".json")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="report file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data