from langchain_tavily import TavilySearch
from app.core.config import TAVILY_API_KEY

tavily_tool = TavilySearch(
    tavily_api_key=TAVILY_API_KEY,
    search_depth="advanced",
    max_results=5,
    exclude_domains=[
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be"
    ],
)

def run_tavily(query: str) -> str:
    return tavily_tool.run(query)

def preprocess_tavily_results(raw_results: dict) -> list:
    cleaned = []
    MAX_CONTENT_LEN = 700
    for r in raw_results.get("results", []):
        content = r.get("content", "").strip()
        score = r.get("score")

        if not content:
            continue

        if score is None or score < 0.7:
            continue

        cleaned.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "score": score,
            "content": content[:MAX_CONTENT_LEN],  # [:MAX_CONTENT_LEN]
        })

    return cleaned

def stringify_search_results(results: list) -> str:
    if not results:
        return "No relevant search results were found."

    print(f"Total documents: {len(results)}\n")

    blocks = []
    for idx, r in enumerate(results, start=1):
        score = r.get("score", "N/A")
        # if isinstance(score, float):
        #     score = f"{score:.2f}"

        print(f"{idx}. {r['title']}")
        print(f"   Score : {score}\n")

        block = (
            f"Title: {r['title']}\n"
            f"Content: {r['content']}"
        )
        blocks.append(block)

    return "\n\n---\n\n".join(blocks)

