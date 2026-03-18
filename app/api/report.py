import json
import os
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from app.core.config import LOG_DIR
from app.report.schema import IntervalReportRequest, IntervalReportFileRequest

router = APIRouter(prefix="/report", tags=["report"])

def get_interval_report_base_dir() -> str:
    return os.path.join(LOG_DIR, "report", "interval")


@router.post("/interval")
def list_interval_reports(req: IntervalReportRequest):
    base_dir = get_interval_report_base_dir()
    date_dir = os.path.join(base_dir, req.date)

    if not os.path.isdir(date_dir):
        raise HTTPException(status_code=404, detail=f"No interval report directory for date={req.date}")

    files = [
        f for f in os.listdir(date_dir)
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
    if not req.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="filename must end with .json")

    base_dir = get_interval_report_base_dir()
    file_path = os.path.join(base_dir, req.date, req.filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="report file not found")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data