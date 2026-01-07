from typing import TypedDict, Optional, List, Dict

class ChatState(TypedDict):
    request_id: str
    thread_id: str
    message: str

    messages: Optional[List[Dict[str, str]]]

    reply: Optional[str]
    elapsed_sec: Optional[float]
    error: Optional[str]
