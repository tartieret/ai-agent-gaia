from langchain_tavily import TavilySearch

import settings

# -----------------------------------------
# Web Search


web_search_tool = TavilySearch(
    max_results=5,
    topic="general",
    include_relevant_snippets=True,
    api_key=settings.TAVILY_API_KEY,
)
