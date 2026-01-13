from langchain_tavily import TavilySearch
from app.core.config import TAVILY_API_KEY

tavily_tool = TavilySearch(
    tavily_api_key=TAVILY_API_KEY,
    search_depth="advanced",
    max_results=5,
)

def run_tavily(query: str) -> str:
    return tavily_tool.run(query)

def preprocess_tavily_results(raw_results: dict) -> list:

    #MAX_CONTENT_LEN = 500 
    cleaned = []

    for r in raw_results.get("results", []):
        content = r.get("content", "").strip()
        if not content:
            continue

        cleaned.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "content": content,#[:MAX_CONTENT_LEN],
        })

    return cleaned

def stringify_search_results(results: list) -> str:
    if not results:
        return "No relevant search results were found."

    blocks = []
    for r in results:
        block = (
            f"Title: {r['title']}\n"
            f"Content: {r['content']}"
        )
        blocks.append(block)

    return "\n\n---\n\n".join(blocks)
