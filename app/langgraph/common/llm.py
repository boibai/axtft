import time, httpx, json
from app.langgraph.common.state import AnalyzeState, ChatState
from app.langgraph.common.schema import ErrorCauseList, AnomalyCauseList
from app.core.config import VLLM_BASE_URL, MODEL_NAME, VLLM_BASE_URL2
from app.report.schema import TenMinuteSummaryReport, DailyReport

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


async def call_report_llm(prompt: list, type: str) :

    start = time.perf_counter()

    if type == "interval" :
        json_schema = TenMinuteSummaryReport.model_json_schema()
    
    elif type == "daily" :
        json_schema = DailyReport.model_json_schema()
    
    payload = {
        "model": MODEL_NAME,
        "messages": prompt,
        "temperature": 0.0,
        "max_tokens": 4096,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cause-list",
                "schema": json_schema,
            },
        },
    }

    resp = await client.post(VLLM_BASE_URL2, json=payload)
    resp.raise_for_status()

    data = resp.json()
    usage = data.get("usage", {})
    
    metadata = {
        "prompt_tokens" : usage.get("prompt_tokens"),
        "completion_tokens" : usage.get("completion_tokens"),
        "total_tokens" : usage.get("total_tokens"),
        "elapsed_sec" : round(time.perf_counter() - start, 3)
    }
    
    # print(json.dumps(data, indent=2, ensure_ascii=False))
    # print(data["choices"][0]["message"]["content"])
    result = json.loads(data["choices"][0]["message"]["content"])

    return result, metadata


async def call_chat_llm(state: ChatState) -> ChatState:
    payload = {
        "model": MODEL_NAME,
        "messages": state["messages"],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    resp = await client.post(VLLM_BASE_URL2, json=payload)
    resp.raise_for_status()

    state["llm_raw"] = resp.json()

    return state