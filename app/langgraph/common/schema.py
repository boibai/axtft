from pydantic import BaseModel, BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
class LogInfo(BaseModel):
    level: str
    logger: str

class ThreadInfo(BaseModel):
    name: str

class ProcessInfo(BaseModel):
    pid: int
    thread: ThreadInfo

class ServiceInfo(BaseModel):
    name: str

class LabelsInfo(BaseModel):
    log_type: str

class EventInfo(BaseModel):
    dataset: str

class ErrorInfo(BaseModel):
    type: str
    message: Optional[str] = None
    stack_trace: str

class MetricPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(alias='@timestamp')
    http_error_rate: float
    latency_p95: int
    latency_p99: int
    service_status: Literal[0, 1]
    cpu_usage: float
    memory_usage: float
    throughput: float
    db_connection_pool: int
    disk_usage: float

class LogEntry(BaseModel):
    timestamp: str = Field(alias='@timestamp')
    log: LogInfo
    process: ProcessInfo
    service: ServiceInfo
    labels: LabelsInfo
    message: str
    event: EventInfo

class AnalyzeErrorRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")  # allow, ignore

    timestamp: str = Field(alias='@timestamp')

    log: LogInfo
    process: ProcessInfo
    service: ServiceInfo
    labels: LabelsInfo
    message: Optional[str] = None
    event: EventInfo

    http_error_rate: float
    latency_p95: float
    latency_p99: float
    service_status: int
    cpu_usage: float
    memory_usage: float
    throughput: float
    db_connection_pool: int
    disk_usage: float

    error: ErrorInfo
    
class AnalyzeAnomalyRequest(BaseModel):

    model_config = ConfigDict(extra="forbid")  # allow, ignore
    metrics: List[MetricPoint] = Field(default_factory=list)
    logs: List[LogEntry] = Field(default_factory=list)
    
class ErrorCauseItem(BaseModel):
    causeId: int
    title: str
    cause: str
    evidence: str
    actionPlan: List[str]

class ErrorCauseList(BaseModel):
    causeList: List[ErrorCauseItem]
    
class AnomalyCauseItem(BaseModel):
    causeId: int
    relatedMetrics : List[str]
    title: str
    cause: str
    evidence: str
    actionPlan: List[str]

class AnomalyCauseList(BaseModel):
    riskLevel: Literal["LOW", "MEDIUM", "HIGH"]
    causeList: List[AnomalyCauseItem]