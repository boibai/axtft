import time, httpx, json
from app.langgraph.common.state import AnalyzeState, ChatState
from app.langgraph.common.schema import CauseList, Decision
from app.core.config import VLLM_BASE_URL, MODEL_NAME
from app.services.memory_store import save_memory

# connect : TCP 연결 수립까지 허용 시간 (서버가 안 살아있거나 네트워크 문제 시 여기서 끊김)
# read : 서버가 응답 바디를 보내기까지 기다리는 최대 시간 (LLM 추론처럼 오래 걸리는 요청에 중요)
# write : 요청 바디를 서버로 전송하는 데 허용되는 시간 (큰 JSON / 로그 payload 전송 시)
# pool : 커넥션 풀에서 사용 가능한 연결을 기다리는 최대 시간 (동시 요청 많을 때 대기 제한)
# max_connections : # 동시에 열 수 있는 최대 TCP 연결 수 (동시 LLM 요청 상한선)
# max_keepalive_connections : Keep-Alive로 유지할 연결 수 (자주 호출되는 서버면 높게 유지)
client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
    limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
)

async def call_analyze_llm(state: AnalyzeState) -> AnalyzeState:
    start = time.perf_counter()

    payload = {
        "model": MODEL_NAME,
        "messages": state["messages"],
        "temperature": 0.0,
        "max_tokens": 4096,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cause-list",
                "schema": CauseList.model_json_schema(),
            },
        },
    }

    resp = await client.post(VLLM_BASE_URL, json=payload)
    resp.raise_for_status()

    data = resp.json()

    state["llm_content"] = data["choices"][0]["message"]["content"]
    state["elapsed_sec"] = round(time.perf_counter() - start, 3)

    usage = data.get("usage", {})
    state["model_name"] = MODEL_NAME
    state["prompt_tokens"] = usage.get("prompt_tokens")
    state["completion_tokens"] = usage.get("completion_tokens")
    state["total_tokens"] = usage.get("total_tokens")

    return state

async def call_chat_llm(state: ChatState) -> ChatState:
    start = time.perf_counter()

    payload = {
        "model": MODEL_NAME,
        "messages": state["messages"],
        "temperature": 0.0,
        "max_tokens": 1024
    }

    try:
        resp = await client.post(VLLM_BASE_URL, json=payload)
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
            [
                {
                    "role": "user",
                    "content": state["message"],
                    "type": "final"
                },
                {
                    "role": "assistant",
                    "content": reply,
                    "type": "final"
                }
            ]
        )


    except Exception as e:
        state.update({
            "reply": None,
            "error": str(e),
            "elapsed_sec": round(time.perf_counter() - start, 3),
        })

    return state

async def call_decision_llm(messages: list) -> dict:
    """
    decision 판단 전용 LLM 호출
    JSON(dict)로 반환
    """
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 4096,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "decision",
                "schema": Decision.model_json_schema(),
            },
        },
    }
    resp = await client.post(VLLM_BASE_URL, json=payload)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    print(content)
    return json.loads(content)