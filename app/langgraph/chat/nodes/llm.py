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

        state["reply"] = reply
        state["elapsed_sec"] = round(time.perf_counter() - start, 3)
        state["error"] = None

        usage = data.get("usage", {})
        state["model_name"] = MODEL_NAME
        state["prompt_tokens"] = usage.get("prompt_tokens")
        state["completion_tokens"] = usage.get("completion_tokens")
        state["total_tokens"] = usage.get("total_tokens")
        
        # memory 저장 (system 제외)
        save_memory(state["thread_id"], state["messages"][1:] + [
            {"role": "assistant", "content": reply}
        ])

    except Exception as e:
        state["reply"] = None
        state["elapsed_sec"] = round(time.perf_counter() - start, 3)
        state["error"] = str(e)

    return state
