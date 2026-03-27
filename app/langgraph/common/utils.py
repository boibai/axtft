import tiktoken
from datetime import datetime
from typing import Any, Mapping, Iterable
from app.core.config import METRIC_FIELDS, LOG_FIELDS

def truncate_by_tokens(text: str, max_tokens: int = 8192, model: str = "gpt-oss-20b") -> str:

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

def build_metrics_block_table(metrics: Iterable) -> str:
    metrics = list(metrics)
    if not metrics:
        return ""

    # 시간 순 정렬
    metrics.sort(key=lambda m: m.timestamp)

    columns = ["timestamp"] + [f for f in METRIC_FIELDS if f != "timestamp"]

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

                value = value.strftime("%H:%M:%S")

            row.append(str(value))

        lines.append(" | ".join(row))

    if len(lines) == 1:
        return ""

    return (
        "\nSYSTEM_METADATA_START\n\n"
        + "\n".join(lines)
        + "\n\nSYSTEM_METADATA_END\n\n"
    )

def _as_dict(obj: Any) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True)

    if hasattr(obj, "dict"):
        return obj.dict(by_alias=True)

    if isinstance(obj, Mapping):
        return dict(obj)

    return {}


def _get_nested(data: dict, path: str) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _parse_ts(ts: Any) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def _format_ts(ts: Any) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(ts)


def _normalize_cell(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return ",".join("" if v is None else str(v) for v in value)

    return str(value).replace("\n", " ").replace("\r", " ").strip()


def format_logs_as_table(logs: list[Any]) -> str:
    lines = []

    normalized_logs = []
    for item in logs:
        log = _as_dict(item)
        ts = _get_nested(log, "log.@timestamp")
        normalized_logs.append((log, _parse_ts(ts)))

    normalized_logs.sort(key=lambda x: x[1])

    header = " | ".join(display for display, _ in LOG_FIELDS)
    lines.append(header)

    for log, _ in normalized_logs:
        row = []

        for display_name, actual_path in LOG_FIELDS:
            value = _get_nested(log, actual_path)

            if actual_path == "log.@timestamp":
                value = _format_ts(value)

            row.append(_normalize_cell(value))

        lines.append(" | ".join(row))

    return "\n".join(lines)