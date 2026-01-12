from typing import TypedDict, Optional, List, Dict, Literal

# class ChatState(TypedDict):
#     request_id: str
#     thread_id: str

#     model_name: str
#     prompt_tokens: Optional[int]
#     completion_tokens: Optional[int]
#     total_tokens: Optional[int]
    
#     message: str

#     messages: Optional[List[Dict[str, str]]]

#     reply: Optional[str]
#     elapsed_sec: Optional[float]
#     error: Optional[str]


class ChatState(TypedDict):
    request_id: str
    thread_id: str

    message: str
    messages: Optional[List[Dict[str, str]]]

    # LLM usage
    model_name: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]

    # agent control
    action: Optional[Literal["direct", "search"]]
    search_query: Optional[str]
    search_result: Optional[str]

    reply: Optional[str]
    elapsed_sec: Optional[float]
    error: Optional[str]
    searched: bool
    searched_for_request: Optional[str] 
    search_used_in_turn: bool

