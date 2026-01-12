# from langgraph.graph import StateGraph, END
# from app.langgraph.chat.state import ChatState

# from app.langgraph.chat.nodes.prompt import build_messages
# from app.langgraph.chat.nodes.llm import call_llm

# graph = StateGraph(ChatState)

# graph.add_node("build_messages", build_messages)
# graph.add_node("call_llm", call_llm)

# graph.set_entry_point("build_messages")
# graph.add_edge("build_messages", "call_llm")
# graph.add_edge("call_llm", END)

# chat_graph = graph.compile()

from langgraph.graph import StateGraph, END
from app.langgraph.chat.state import ChatState

from app.langgraph.chat.nodes.prompt import build_messages, build_search_messages
from app.langgraph.chat.nodes.llm import call_llm
from app.langgraph.chat.nodes.decide_action import decide_action
from app.langgraph.chat.nodes.search import run_search

graph = StateGraph(ChatState)

graph.add_node("decide_action", decide_action)
graph.add_node("build_messages", build_messages)
graph.add_node("search", run_search)
graph.add_node("build_search_messages", build_search_messages)
graph.add_node("call_llm", call_llm)

graph.set_entry_point("decide_action")

graph.add_conditional_edges(
    "decide_action",
    lambda s: s["action"],
    {
        "direct": "build_messages",
        "search": "search",
    },
)

# direct path
graph.add_edge("build_messages", "call_llm")

# search path
graph.add_edge("search", "build_search_messages")
graph.add_edge("build_search_messages", "call_llm")

# call_llm 뒤에는 무조건 종료
graph.add_edge("call_llm", END)

chat_graph = graph.compile()