from pydantic import BaseModel
from typing import List, Optional, Literal

class AnalyzeRequest(BaseModel):
    message: str

class CauseItem(BaseModel):
    causeId: int
    title: str
    cause: str
    evidence: str
    actionPlan: str  # List[str]

class CauseList(BaseModel):
    causeList: List[CauseItem]

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class Decision(BaseModel):
    action: Literal["direct", "search"]
    search_query: Optional[str]
