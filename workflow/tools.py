import re

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

web_search_tool = DuckDuckGoSearchResults(max_results=10)


@tool
def fetch_url_content(url: str) -> dict[str, int | str]:
    """
    Fetch the content of a URL using a headless browser to handle JavaScript-rendered content.

    Args:
        url: The URL to fetch the content of.

    Returns:
        dict[str, int|str]: A dictionary containing the status code, content of the URL, and any error messages.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Navigate to the URL with a timeout
            response = page.goto(url, timeout=30000, wait_until='networkidle')

            if response is None:
                browser.close()
                return {
                    "url": url,
                    "status_code": 0,
                    "content": "Failed to load page"
                }

            status_code = response.status

            # Wait a bit for any dynamic content to load
            page.wait_for_timeout(2000)

            # Get the page content after JavaScript execution
            content_html = page.content()

            browser.close()

            # Parse the content with BeautifulSoup
            beautiful_soup = BeautifulSoup(content_html, 'html.parser')

            # Remove script and style elements
            for script in beautiful_soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = beautiful_soup.get_text(separator=" ", strip=True)

            # Clean up extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Limit content size to avoid overwhelming the LLM
            max_content_length = 50000  # ~50k characters
            if len(text) > max_content_length:
                text = text[:max_content_length] + "... (content truncated)"

            return {
                "url": url,
                "status_code": status_code,
                "content": text if text else "No content found in the URL"
            }

    except PlaywrightTimeoutError:
        return {
            "url": url,
            "status_code": 408,
            "content": "Request timeout - page took too long to load"
        }
    except (OSError, RuntimeError) as e:
        # Handle network errors, browser launch errors, etc.
        return {
            "url": url,
            "status_code": 0,
            "content": f"Error fetching URL content: {str(e)}"
        }


@tool
def extract_url_context(markdown_content: str, url: str) -> dict[str, str]:
    """
    Extract the section context where a URL appears in the markdown content.

    Args:
        markdown_content: The markdown content containing the URL.
        url: The URL to find the context for.

    Returns:
        dict[str, str]: A dictionary containing the section name, section content, and surrounding context.
    """
    try:
        lines = markdown_content.split('\n')
        url_line_idx = -1

        # Find the line containing the URL
        for idx, line in enumerate(lines):
            if url in line:
                url_line_idx = idx
                break

        if url_line_idx == -1:
            return {
                "url": url,
                "section": "Unknown",
                "context": "URL not found in content"
            }

        # Find the current section by looking backwards for the nearest heading
        current_section = "Unknown"

        for idx in range(url_line_idx, -1, -1):
            line = lines[idx].strip()
            if line.startswith('#'):
                # Found the section heading
                current_section = line.lstrip('#').strip()
                break

        # Extract surrounding context (5 lines before and after)
        context_start = max(0, url_line_idx - 5)
        context_end = min(len(lines), url_line_idx + 6)
        context = '\n'.join(lines[context_start:context_end])

        # Determine section type
        section_lower = current_section.lower()
        section_type = "other"

        if any(keyword in section_lower for keyword in ['intro', 'overview', 'about', 'service info', 'common use', 'compatibility']):
            section_type = "product_info"
        elif any(keyword in section_lower for keyword in ['setup', 'configuration', 'install', 'set up', 'vendor set up', 'kibana set up']):
            section_type = "setup"
        elif any(keyword in section_lower for keyword in ['documentation', 'reference', 'resources', 'documentation sites']):
            section_type = "documentation"
        elif any(keyword in section_lower for keyword in ['troubleshoot', 'error', 'issue']):
            section_type = "troubleshooting"

        return {
            "url": url,
            "section": current_section,
            "section_type": section_type,
            "context": context
        }

    except (ValueError, IndexError, AttributeError) as e:
        # Handle parsing errors
        return {
            "url": url,
            "section": "Unknown",
            "section_type": "other",
            "context": f"Error extracting context: {str(e)}"
        }
