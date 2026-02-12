# app/langgraph/common/chat_memory.py

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

    # ===============================
    # 내부 유틸
    # ===============================

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

    # ===============================
    # 공개 메서드
    # ===============================

    def get(self, thread_id: str) -> List[dict]:
        raw = self.redis.get(self._redis_key(thread_id))
        if not raw:
            return []
        return json.loads(raw)

    def save(self, thread_id: str, messages: List[dict]):
        
        prev = self.get(thread_id)
        filtered = []
        print(messages)
        for m in messages:
            if m.get("type") != "final":
                continue
            if m.get("role") not in ("user", "assistant"):
                continue

            content = m.get("content")

            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)

            content = self._strip_search_result(content)

            filtered.append({
                "role": m["role"],
                "content": content
            })

        merged = prev + filtered

        # sliding window (토큰 기준)
        while merged and self._total_tokens(merged) > self.max_tokens:
            merged.pop(0)

        self.redis.set(
            self._redis_key(thread_id),
            json.dumps(merged, ensure_ascii=False)
        )

    def clear(self, thread_id: str):
        self.redis.delete(self._redis_key(thread_id))
