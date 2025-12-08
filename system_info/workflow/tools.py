from typing import Tuple

import requests
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from bs4 import BeautifulSoup

web_search_tool = DuckDuckGoSearchResults(max_results=10)


@tool
def fetch_url_content(url: str) -> dict[str, int | str]:
    """
    Fetch the content of a URL.

    Args:
        url: The URL to fetch the content of.

    Returns:
        dict[str, int|str]: A dictionary containing the status code and the content of the URL as a string.
    """
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return {"status_code": response.status_code, "content": "Error fetching URL content"}

    beautiful_soup = BeautifulSoup(response.text, 'html.parser')
    text = beautiful_soup.get_text(separator=" ", strip=True)

    return {
        "url": url,
        "status_code": response.status_code,
        "content": text if text else "No content found in the URL"
    }
