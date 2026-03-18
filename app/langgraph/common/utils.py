import tiktoken
from datetime import datetime
from typing import Any, Mapping, Iterable
from app.core.config import METRIC_FIELDS, LOG_FIELDS

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

def format_logs_as_table(logs: list[Any]) -> str:
    lines = []

    header = " | ".join(LOG_FIELDS)
    lines.append(header)

    for item in logs:
        log = _as_dict(item)

        ts = log.get("@timestamp", "")
        level = (log.get("log") or {}).get("level", "")
        logger = (log.get("log") or {}).get("logger", "")
        #pid = (log.get("process") or {}).get("pid", "")
        #thread = ((log.get("process") or {}).get("thread") or {}).get("name", "")
        #service = (log.get("service") or {}).get("name", "")
        message = log.get("message", "")

        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = dt.strftime("%m-%dT%H:%M:%S")
            except Exception:
                ts = ts  # 파싱 실패 시 원본 유지

        row = [
            ts,
            #str(service),
            #str(pid),
            #str(thread),
            str(level),
            str(logger),
            str(message),
        ]

        lines.append(" | ".join(row).strip())

    return "\n".join(lines)

def build_metrics_block_table(metrics: Iterable) -> str:
    metrics = list(metrics)
    if not metrics:
        return ""

    # 시간 순 정렬
    metrics.sort(key=lambda m: m.timestamp)

    # 출력 컬럼 (timestamp 포함)
    columns = ["timestamp"] + [f for f in METRIC_FIELDS if f != "timestamp"]

    # 헤더 1줄
    header = " | ".join(columns)

    lines = [header]

    for m in metrics:
        row = []
        for field in columns:
            value = getattr(m, field, None)

            if value is None:
                row.append("")
                continue

            if field == "timestamp":
                # MM-DDTHH:MM:SS 형태
                value = value.strftime("%m-%dT%H:%M")

            row.append(str(value))

        lines.append(" | ".join(row))

    if len(lines) == 1:
        return ""

    return (
        "\nSYSTEM_METADATA_START\n\n"
        + "\n".join(lines)
        + "\n\nSYSTEM_METADATA_END\n\n"
    )
    
# def stringify_history(history):

#     lines = []

#     for h in history:
#         if h["role"] not in ("user", "assistant"):
#             continue

#         lines.append(f'{h["role"]}: {h["content"]}')
        
#     return "\n".join(lines)

