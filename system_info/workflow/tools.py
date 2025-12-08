from langchain_community.tools import DuckDuckGoSearchResults

web_search_tool = DuckDuckGoSearchResults(max_results=10)
