from langchain_tavily import TavilySearch
from app.core.config import TAVILY_API_KEY

tavily_tool = TavilySearch(
    tavily_api_key=TAVILY_API_KEY,
    search_depth="advanced",
    max_results=5,
)

def run_tavily(query: str) -> str:
    return tavily_tool.run(query)
