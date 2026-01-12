import json
import httpx
from app.langgraph.chat.state import ChatState
from app.core.config import VLLM_BASE_URL, MODEL_NAME
from app.models.schema import Decision
from app.core.config import AGENT_DECISION_PROMPT_PATH

with open(AGENT_DECISION_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

async def decide_action(state: ChatState) -> ChatState:
    
    if state.get("search_used_in_turn"):
        state["action"] = "direct"
        return state
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["message"]},
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 128,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "decision",
                "schema": Decision.model_json_schema(),
            },
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            VLLM_BASE_URL,
            json=payload
        )
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]

    try:
        decision = json.loads(content)
        state["action"] = decision["action"]
        state["search_query"] = decision.get("search_query")
    except Exception:
        state["action"] = "direct"

    print(state["action"])

    return state
