from typing import TypedDict, Optional, Any, Dict, List

class AnalyzeState(TypedDict):
    request_id: str
    message: str

    # prompt / messages
    messages: List[Dict[str, str]]

    # LLM raw output
    llm_content: Optional[str]

    # parsed result
    parsed_json: Optional[Dict[str, Any]]

    # meta
    client_ip: Optional[str]
    client_port: Optional[int]
    elapsed_sec: Optional[float]
    error: Optional[str]
