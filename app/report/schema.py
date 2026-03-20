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
    
class TopIncident(BaseModel):
    time: str 
    level: Literal["low", "medium", "high"]
    summary: str
    impact: str

class PatternItem(BaseModel):
    type: str
    summary: str

class TimelineCompactItem(BaseModel):
    time: str
    level: Literal["low", "medium", "high"]
    summary: str

class ActionItem(BaseModel):
    priority: Literal["P1", "P2", "P3"]
    action: str

class Stats(BaseModel):
    low: int
    medium: int
    high: int
    service_down: bool
    latency_issue: bool

class DailyReport(BaseModel):
    overall_level: Literal["low", "medium", "high"]
    summary: str
    top_incident: TopIncident
    patterns: List[PatternItem]
    timeline_compact: List[TimelineCompactItem]
    actions: List[ActionItem]