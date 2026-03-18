from typing import List, Literal
from pydantic import BaseModel, Field

class EventSummary(BaseModel):
    start_time: str
    end_time: str
    level: Literal["low", "medium", "high"]
    summary: str


class TenMinuteSummaryReport(BaseModel):
    level: Literal["low", "medium", "high"]
    summary: str
    events: List[EventSummary]


class IntervalReportRequest(BaseModel):
    date: str
    
class IntervalReportFileRequest(BaseModel):
    date: str
    filename: str