from typing import List
import json, re
from app.core.redis import redis_client

MAX_MEMORY_TOKENS = 4096
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)

def total_tokens(messages: List[dict]) -> int:
    return sum(estimate_tokens(m["content"]) for m in messages)

def _redis_key(thread_id: str) -> str:
    return f"chat:memory:{thread_id}"

def get_memory(thread_id: str) -> List[dict]:
    raw = redis_client.get(_redis_key(thread_id))
    if not raw:
        return []
    return json.loads(raw)

def strip_search_result(text: str) -> str:
    pattern = re.compile(
        r"-{32,}\s*SEARCH RESULTS\s*-{32,}.*?-{32,}\s*USER QUESTION\s*-{32,}",
        re.DOTALL
    )
    return re.sub(pattern, "", text).strip()

def save_memory(thread_id: str, messages: List[dict]):
    prev = get_memory(thread_id)
    filtered = []

    for m in messages:
        if m.get("type") != "final":
            continue
        if m.get("role") not in ("user", "assistant"):
            continue

        content = m.get("content")
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        filtered.append({
            "role": m["role"],
            "content": content
        })

    merged = prev + filtered

    while merged and total_tokens(merged) > MAX_MEMORY_TOKENS:
        merged.pop(0)

    redis_client.set(
        _redis_key(thread_id),
        json.dumps(merged, ensure_ascii=False)
    )
