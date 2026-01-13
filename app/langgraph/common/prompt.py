from app.langgraph.common.state import AnalyzeState, ChatState
from app.core.config import ANALYZE_SYSTEM_PROMPT_PATH, CHAT_SYSTEM_PROMPT_PATH, TAVILY_CHAT_SYSTEM_PROMPT_PATH, AGENT_DECISION_PROMPT_PATH
from app.services.memory_store import get_memory
from app.langgraph.common.utils import stringify_history
import json
from string import Template
from datetime import date

# system prompt 로드
with open(ANALYZE_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    system_prompt = f.read()

with open(CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_messages_prompt = Template(f.read())

with open(TAVILY_CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_tavily_messages_prompt = Template(f.read())

with open(AGENT_DECISION_PROMPT_PATH, "r", encoding="utf-8") as f:
    decision_system_prompt = Template(f.read())

def build_anaylze_messages(state: AnalyzeState) -> AnalyzeState:
    state["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user","content": f"""Analyze ONLY the log content below.\nLOG_INPUT_START\n{state["message"]}\nLOG_INPUT_END"""},
    ]
    return state

def build_chat_messages(state: ChatState) -> ChatState:
    history = get_memory(state["thread_id"])
    history_text = stringify_history(history)

    system_text = build_messages_prompt.safe_substitute(
        conversation_history=history_text,
        user_question=state["message"],
    )

    state["messages"] = [
        {
            "role": "system",
            "content": system_text,
            "type": "chat_system"
        },
        {
            "role": "user",
            "content": state["message"],
            "type": "final"
        }
    ]

    print(state)
    return state


def build_search_messages(state: ChatState) -> ChatState:
    history = get_memory(state["thread_id"])
    history_text = stringify_history(history)

    today = date.today().isoformat()

    system_text = build_messages_prompt.safe_substitute(
        today=today
    )

    state["messages"] = [
        # system 프롬프트 (규칙 / 지침)
        {
            "role": "system",
            "content": system_text
        },

        # 검색 결과: user role + search_context
        {
            "role": "user",
            "content": f"""
--------------------------------
CONVERSATION HISTORY
--------------------------------
{history_text}

--------------------------------
SEARCH RESULTS
--------------------------------
{state["search_result"]}
""",
            "type": "search_context"
        },

        # 실제 사용자 질문: user role + final
        {
            "role": "user",
            "content": state["message"],
            "type": "final"
        }
    ]

    print(state)
    return state


def build_decision_messages(state: ChatState) -> list:
    """
    decision 판단을 위한 messages 생성
    """
    history = get_memory(state["thread_id"])
    history_text = stringify_history(history)

    system_text = decision_system_prompt.safe_substitute(
        conversation_history=history_text,
        user_question=state["message"],
    )

    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": 
f"""
--------------------------------
CONVERSATION HISTORY
--------------------------------
{history_text}

--------------------------------
USER QUESTION
--------------------------------
{state["message"]}

"""}]