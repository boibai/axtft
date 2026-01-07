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
    messages: system 제외한 [user, assistant, ...]
    """
    while messages and total_tokens(messages) > MAX_MEMORY_TOKENS:
        messages.pop(0)

    _CHAT_MEMORY[thread_id] = messages
