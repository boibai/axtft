from typing import TypedDict, Optional, Any, Dict, List, Literal

class AnalyzeErrorState(TypedDict):

    request_id: str
    message: str
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

    request_id: str
    thread_id: str
    message: str
    messages: Optional[List[Dict[str, str]]]
    model_name: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    action: Optional[Literal["direct", "search"]]
    search_query: Optional[str]
    search_result: Optional[str]
    reply: Optional[str]
    elapsed_sec: Optional[float]
    error: Optional[str]
    searched: bool
    searched_for_request: Optional[str]
    search_used_in_turn: bool
