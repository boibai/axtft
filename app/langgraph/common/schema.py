from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

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
    model_config = ConfigDict(extra="allow")

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

# class LogEntry(BaseModel):
#     timestamp: str = Field(alias='@timestamp')
#     log: LogInfo
#     process: ProcessInfo
#     service: ServiceInfo
#     labels: LabelsInfo
#     message: str
#     event: EventInfo

class AnalyzeErrorRequest(BaseModel):

    model_config = ConfigDict(extra="allow")

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

class AnalyzeErrorMessageRequest(BaseModel):

    model_config = ConfigDict(extra="allow") 
    message: str



class Thread(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None


class Process(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pid: Optional[int] = None
    thread: Optional[Thread] = None


class Log(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: Optional[str] = Field(default=None, alias='@timestamp')
    message: Optional[str] = None
    level: Optional[str] = None
    logger: Optional[str] = None


class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None


class Labels(BaseModel):
    model_config = ConfigDict(extra="ignore")

    log_type: Optional[str] = None


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dataset: Optional[str] = None


class LogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    log: Optional[Log] = None
    process: Optional[Process] = None
    service: Optional[Service] = None
    labels: Optional[Labels] = None
    event: Optional[Event] = None
    

class AnalyzeAnomalyRequest(BaseModel):

    model_config = ConfigDict(extra="allow")
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
    
    


class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    history_count: int