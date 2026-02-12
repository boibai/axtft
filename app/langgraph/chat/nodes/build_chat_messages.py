from app.langgraph.common.state import  ChatState
from app.core.config import  TAVILY_CHAT_SYSTEM_PROMPT_PATH, CHAT_SYSTEM_PROMPT_PATH, AGENT_DECISION_PROMPT_PATH
from app.langgraph.common.utils import stringify_history
from string import Template
from datetime import date
from app.langgraph.common.chat_memory import ChatMemory
from app.core.redis import get_redis_client

redis_client = get_redis_client()
chat_memory = ChatMemory(redis_client)

with open(CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_messages_prompt = Template(f.read())

with open(AGENT_DECISION_PROMPT_PATH, "r", encoding="utf-8") as f:
    decision_system_prompt = Template(f.read())

with open(TAVILY_CHAT_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    build_tavily_messages_prompt = Template(f.read())


def build_chat_messages(state: ChatState) -> ChatState:
    history = chat_memory.get(state["thread_id"])
    system_text = build_messages_prompt.safe_substitute()
    state["messages"] = [
        {
            "role": "system",
            "content": system_text,
            "type": "chat_system"
        },
        *history, 
        {
            "role": "user",
            "content": state["message"],
            "type": "final"
        }
    ]

    return state


def build_decision_messages(state: ChatState) -> list:
    print("\n"+"="*20+" DECISION NODE START\n")
    history = chat_memory.get(state["thread_id"])
    system_text = decision_system_prompt.safe_substitute()
    
    return [
        {
            "role": "system",
            "content": system_text
        },
        *history,
        {
            "role": "user",
            "content": state["message"]
        }
    ]

def build_search_messages(state: ChatState) -> ChatState:
    
    today = date.today().isoformat()

    system_text = build_tavily_messages_prompt.safe_substitute(
        today=today
    )

    state["messages"] = [
        {
            "role": "system",
            "content": system_text
        },

        {
            "role": "user",
            "content": f"""
--------------------------------
SEARCH RESULTS
--------------------------------
{state["search_result"]}
""",
            "type": "search_context"
        },
        
        {
            "role": "user",
            "content": state["message"],
            "type": "final"
        }
    ]
    return state