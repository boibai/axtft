from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    message: str

class CauseItem(BaseModel):
    causeId: int
    title: str
    cause: str
    evidence: str
    actionPlan: List[str]

class CauseList(BaseModel):
    causeList: List[CauseItem]

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
