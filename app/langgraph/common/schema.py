from pydantic import BaseModel, BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict, Any

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
    
    http_error_rate: float
    latency_p95: float
    latency_p99: float
    service_status: int
    cpu_usage: float
    memory_usage: float
    throughput: float
    db_connection_pool: int
    disk_usage: float
    logs: List[LogEntry]

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
    causeList: List[AnomalyCauseItem]
