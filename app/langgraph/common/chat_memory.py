from typing import List
import json
import re

class ChatMemory:
    
    def __init__(
         self,
         redis_client,
         max_memory_tokens: int = 4096,
         chars_per_token: int = 4,
     ):
         self.redis = redis_client
         self.max_tokens = max_memory_tokens
         self.chars_per_token = chars_per_token
 
    def _redis_key(self, thread_id: str) -> str:
        return f"chat:memory:{thread_id}"
 
    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // self.chars_per_token)
 
    def _total_tokens(self, messages: List[dict]) -> int:
        return sum(self._estimate_tokens(m["content"]) for m in messages)
 
    def _strip_search_result(self, text: str) -> str:
        pattern = re.compile(
            r"-{32,}\s*SEARCH RESULTS\s*-{32,}.*?-{32,}\s*USER QUESTION\s*-{32,}",
            re.DOTALL
        )
        return re.sub(pattern, "", text).strip()
 
    def get(self, thread_id: str) -> List[dict]:
        raw = self.redis.get(self._redis_key(thread_id))
        if not raw:
            return []
        return json.loads(raw)
 

    def _normalize_message(self, message: dict) -> dict | None:
        role = message.get("role")
        content = message.get("content")
 
        if message.get("type") == "final":
            role = message.get("role")
            content = message.get("content")
 
        if role not in ("user", "assistant"):
           return None
 
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
 

        return {
            "role": role,
            "content": self._strip_search_result(content)
        }
 
    def _trim_by_tokens(self, messages: List[dict]) -> List[dict]:
        merged = list(messages)
        while merged and self._total_tokens(merged) > self.max_tokens:
            merged.pop(0)
        return merged

    def set(self, thread_id: str, messages: List[dict]):
        normalized = []
        for message in messages:
            parsed = self._normalize_message(message)
            if parsed is None:
                continue
            normalized.append(parsed)

        trimmed = self._trim_by_tokens(normalized)
        self.redis.set(
             self._redis_key(thread_id),
             json.dumps(trimmed, ensure_ascii=False)
         )

    def save(self, thread_id: str, messages: List[dict]):
        prev = self.get(thread_id)

        filtered = []
        for message in messages:
            parsed = self._normalize_message(message)
            if parsed is None:
                continue
            filtered.append(parsed)

        merged = self._trim_by_tokens(prev + filtered)
 
        self.redis.set(
             self._redis_key(thread_id),
             json.dumps(merged, ensure_ascii=False)
         )
 
    def append_turn(self, thread_id: str, user_message: str, assistant_message: str):
        self.save(thread_id, [
             {"role": "user", "content": user_message},
             {"role": "assistant", "content": assistant_message},
         ])

    def clear(self, thread_id: str):
        self.redis.delete(self._redis_key(thread_id))