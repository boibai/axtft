from typing import TypedDict, Optional, List, Dict

class ChatState(TypedDict):
    request_id: str
    thread_id: str

    model_name: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    
    message: str

    messages: Optional[List[Dict[str, str]]]

    reply: Optional[str]
    elapsed_sec: Optional[float]
    error: Optional[str]
