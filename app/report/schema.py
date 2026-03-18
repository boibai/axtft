from typing import List, Literal
from pydantic import BaseModel, Field

class EventSummary(BaseModel):
    start_time: str = Field(..., description="특이 구간 시작 시각")
    end_time: str = Field(..., description="특이 구간 종료 시각")
    level: Literal["low", "medium", "high"] = Field(..., description="구간 심각도")
    summary: str = Field(..., description="구간 요약")


class TenMinuteSummaryReport(BaseModel):
    level: Literal["normal", "low", "medium", "high"] = Field(..., description="10분 전체 수준")
    summary: str = Field(..., description="10분 전체 요약")
    events: List[EventSummary] = Field(default_factory=list, description="특이 구간 목록")