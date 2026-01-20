from langgraph.graph import StateGraph, END
from app.langgraph.common.state import AnalyzeState
from app.langgraph.common.llm import call_analyze_llm

from app.langgraph.analyze.nodes.build_anaylze_messages import build_anaylze_messages
from app.langgraph.analyze.nodes.parse import parse_json
from app.langgraph.analyze.nodes.validate import validate_schema

graph = StateGraph(AnalyzeState)

graph.add_node("build_prompt", build_anaylze_messages)
graph.add_node("call_llm", call_analyze_llm)
graph.add_node("parse_json", parse_json)
graph.add_node("validate_schema", validate_schema)

graph.set_entry_point("build_prompt")

graph.add_edge("build_prompt", "call_llm")
graph.add_edge("call_llm", "parse_json")
graph.add_edge("parse_json", "validate_schema")
graph.add_edge("validate_schema", END)

analyze_graph = graph.compile()
