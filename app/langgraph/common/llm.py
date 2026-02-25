import time, httpx, json
from app.langgraph.common.state import AnalyzeState
from app.langgraph.common.schema import ErrorCauseList, AnomalyCauseList
from app.core.config import VLLM_BASE_URL, MODEL_NAME
from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)

# 비동기 HTTP 클라이언트 전역 생성 ( 재사용을 통해 커넥션 풀 활용 및 성능 최적화 )
client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=5.0,   # TCP 연결 수립 최대 대기 시간
        read=120.0,    # 응답 바디 수신 최대 대기 시간 (LLM 추론 고려)
        write=30.0,    # 요청 바디 전송 최대 시간
        pool=5.0       # 커넥션 풀에서 대기 가능한 최대 시간
    ),
    limits=httpx.Limits(
        max_connections=50,          # 동시에 열 수 있는 최대 TCP 연결 수
        max_keepalive_connections=20 # Keep-Alive 유지 연결 수
    ),
)


async def call_analyze_error_llm(state: AnalyzeState) -> AnalyzeState:

    start = time.perf_counter()

    payload = {
        "model": MODEL_NAME,
        "messages": state["messages"],
        "temperature": 0.0,
        "max_tokens": 4096,
        # LLM 출력이 반드시 CauseList 스키마를 따르도록 강제
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cause-list",
                "schema": ErrorCauseList.model_json_schema(),
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


async def call_analyze_anomaly_llm(state: AnalyzeState) -> AnalyzeState:

    start = time.perf_counter()

    payload = {
        "model": MODEL_NAME,
        "messages": state["messages"],
        "temperature": 0.0,
        "max_tokens": 4096,
        # LLM 출력이 반드시 CauseList 스키마를 따르도록 강제
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cause-list",
                "schema": AnomalyCauseList.model_json_schema(),
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