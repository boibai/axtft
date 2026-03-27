from typing import TypedDict, Optional, Any, Dict, List, Literal
from app.langgraph.common.schema import AnalyzeErrorRequest, ChatRequest

class AnalyzeState(TypedDict):

    request_id: str
    message: AnalyzeErrorRequest
    messages: List[Dict[str, str]]
    llm_content: Optional[str]
    model_name: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    parsed_json: Optional[Dict[str, Any]]
    client_ip: Optional[str]
    client_port: Optional[int]
    elapsed_sec: Optional[float]
    error: Optional[str]
    
class ChatState(TypedDict):

    thread_id: str
    request: ChatRequest
    messages: List[Dict[str, str]]
    llm_raw: Dict[str, Any]
    answer: Optional[str]
    history_count: Optional[int]
    error: Optional[str]