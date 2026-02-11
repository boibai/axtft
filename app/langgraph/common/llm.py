import time, httpx, json
from app.langgraph.common.state import AnalyzeState, ChatState
from app.langgraph.common.schema import CauseList, Decision
from app.core.config import VLLM_BASE_URL, MODEL_NAME
from app.langgraph.common.chat_memory import save_memory

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
        "max_tokens": 2048,
        # LLM 출력이 반드시 CauseList 스키마를 따르도록 강제
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
        "max_tokens": 4096
    }
    
    print("\n" + "=" * 20 + " LLM PROMPT START")
    print(json.dumps(state["messages"], ensure_ascii=False, indent=2))
    print("=" * 20 + " LLM PROMPT END\n")
    
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
    검색 필요 여부를 판단하는 decision 전용 LLM 호출 함수
    JSON(dict) 형태로 결과 반환
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

    result = json.loads(content)

    print(f"- action : {result.get('action')}")
    print(f"- search query : {result.get('search_query')}")

    return result