from langgraph.graph import StateGraph, END
from app.langgraph.common.state import AnalyzeErrorState
from app.langgraph.common.llm import call_analyze_error_llm
from app.langgraph.analyze.error.nodes.build_analyze_messages import build_analyze_messages
from app.langgraph.analyze.error.nodes.parse import parse_json
from app.langgraph.analyze.error.nodes.validate import validate_schema

graph = StateGraph(AnalyzeErrorState)

graph.add_node("build_prompt", build_analyze_messages)
graph.add_node("call_llm", call_analyze_error_llm)
graph.add_node("parse_json", parse_json)
graph.add_node("validate_schema", validate_schema)

graph.set_entry_point("build_prompt")

graph.add_edge("build_prompt", "call_llm")
graph.add_edge("call_llm", "parse_json")
graph.add_edge("parse_json", "validate_schema")
graph.add_edge("validate_schema", END)

analyze_graph = graph.compile()
