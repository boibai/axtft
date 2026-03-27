from langgraph.graph import StateGraph, END
from app.langgraph.common.state import ChatState
from app.langgraph.chat.nodes.build_chat_messages import build_chat_messages
from app.langgraph.common.llm import call_chat_llm
from app.langgraph.chat.nodes.extract_answer import extract_answer
from app.langgraph.chat.nodes.save_chat_memory import save_chat_memory

graph = StateGraph(ChatState)

graph.add_node("build_messages", build_chat_messages)
graph.add_node("call_llm", call_chat_llm)
graph.add_node("extract_answer", extract_answer)
graph.add_node("save_memory", save_chat_memory)

graph.set_entry_point("build_messages")

graph.add_edge("build_messages", "call_llm")
graph.add_edge("call_llm", "extract_answer")
graph.add_edge("extract_answer", "save_memory")
graph.add_edge("save_memory", END)

chat_graph = graph.compile()