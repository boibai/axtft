from typing import TypedDict, Optional, Any, Dict, List

class AnalyzeState(TypedDict):
    request_id: str
    message: str

    # prompt / messages
    messages: List[Dict[str, str]]

    # LLM raw output
    llm_content: Optional[str]
    llm_content: str
    model_name: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    
    # parsed result
    parsed_json: Optional[Dict[str, Any]]

    # meta
    client_ip: Optional[str]
    client_port: Optional[int]
    elapsed_sec: Optional[float]
    error: Optional[str]
