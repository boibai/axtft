from langgraph.graph import StateGraph, END
from app.langgraph.chat.state import ChatState

from app.langgraph.chat.nodes.prompt import build_messages
from app.langgraph.chat.nodes.llm import call_llm

graph = StateGraph(ChatState)

graph.add_node("build_messages", build_messages)
graph.add_node("call_llm", call_llm)

graph.set_entry_point("build_messages")
graph.add_edge("build_messages", "call_llm")
graph.add_edge("call_llm", END)

chat_graph = graph.compile()
