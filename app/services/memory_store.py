from typing import Dict, List

_CHAT_MEMORY: Dict[str, List[dict]] = {}

MAX_MEMORY_TOKENS = 4096
CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)

def total_tokens(messages: List[dict]) -> int:
    return sum(estimate_tokens(m["content"]) for m in messages)

def get_memory(thread_id: str) -> List[dict]:
    return _CHAT_MEMORY.get(thread_id, [])

def save_memory(thread_id: str, messages: List[dict]):
    """
    Store ONLY user / assistant messages.
    System messages must NEVER be stored.
    """

    # role whitelist
    filtered = [
        {
            "role": m["role"],
            "content": m["content"]
        }
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]

    # content는 반드시 str
    for m in filtered:
        if not isinstance(m["content"], str):
            m["content"] = json.dumps(m["content"], ensure_ascii=False)

    # token limit 관리
    while filtered and total_tokens(filtered) > MAX_MEMORY_TOKENS:
        filtered.pop(0)

    _CHAT_MEMORY[thread_id] = filtered
