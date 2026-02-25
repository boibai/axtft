import tiktoken
from typing import Any, Mapping

def truncate_by_tokens(text: str, max_tokens: int = 4000, model: str = "gpt-oss-20b") -> str:

    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return text

    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)

    return truncated_text + "\n\n[TRUNCATED_DUE_TO_TOKEN_LIMIT]"

def count_tokens(text: str, model: str = "gpt-oss-20b") -> int:

    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    
    return len(tokens)


def _as_dict(obj: Any) -> dict:
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True)
    # Pydantic v1
    if hasattr(obj, "dict"):
        return obj.dict(by_alias=True)
    # 이미 dict/Mapping이면
    if isinstance(obj, Mapping):
        return dict(obj)
    # 마지막 fallback
    return {}

def format_logs_as_text(logs: list[Any]) -> str:
    lines = []

    for item in logs:
        log = _as_dict(item)

        ts = log.get("@timestamp", "")
        level = (log.get("log") or {}).get("level", "")
        logger = (log.get("log") or {}).get("logger", "")

        pid = (log.get("process") or {}).get("pid", "")
        thread = ((log.get("process") or {}).get("thread") or {}).get("name", "")
        service = (log.get("service") or {}).get("name", "")

        message = log.get("message", "")

        line = (
            f"{ts} | {service} | pid={pid} | thread={thread} | "
            f"{level} | {logger} | {message}"
        )
        lines.append(line.strip())

    return "\n".join(lines)

# def stringify_history(history):

#     lines = []

#     for h in history:
#         if h["role"] not in ("user", "assistant"):
#             continue

#         lines.append(f'{h["role"]}: {h["content"]}')
        
#     return "\n".join(lines)

