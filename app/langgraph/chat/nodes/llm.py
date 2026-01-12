import httpx
import time
from app.langgraph.chat.state import ChatState
from app.core.config import VLLM_BASE_URL, MODEL_NAME
from app.services.memory_store import save_memory

client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
    limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
)

async def call_llm(state: ChatState) -> ChatState:
    start = time.perf_counter()

    try:
        resp = await client.post(
            VLLM_BASE_URL,
            json={
                "model": MODEL_NAME,
                "messages": state["messages"],
                "temperature": 0.0,
                "max_tokens": 1024,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        state.update({
            "reply": reply,
            "model_name": MODEL_NAME,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "elapsed_sec": round(time.perf_counter() - start, 3),
            "error": None,
        })

        save_memory(
            state["thread_id"],
            state["messages"][1:] + [{"role": "assistant", "content": reply}],
        )

    except Exception as e:
        state.update({
            "reply": None,
            "error": str(e),
            "elapsed_sec": round(time.perf_counter() - start, 3),
        })

    return state