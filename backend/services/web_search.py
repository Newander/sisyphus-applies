import asyncio
import logging

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information. "
            "Use this when you need up-to-date facts about a company, job market, technology, "
            "or anything that may have changed since your training data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                }
            },
            "required": ["query"],
        },
    },
}


def _search_sync(query: str, max_results: int) -> str:
    from duckduckgo_search import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        logger.warning("Web search failed query=%r err=%s", query, exc)
        return f"Search failed: {exc}"

    if not results:
        return "No results found."

    lines = []
    for r in results:
        lines.append(f"**{r['title']}**\n{r['href']}\n{r['body']}")
    return "\n\n".join(lines)


async def search(query: str, max_results: int = 5) -> str:
    logger.info("Web search query=%r max_results=%s", query, max_results)
    result = await asyncio.to_thread(_search_sync, query, max_results)
    logger.info("Web search done query=%r chars=%s", query, len(result))
    return result
