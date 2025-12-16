import re
from typing import Any
from functools import partial

from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .prompts import web_page_content_summarizer_prompt
from .constants import DEBUG, flash_llm

web_search_tool = DuckDuckGoSearchResults(max_results=10, verbose=DEBUG)


@tool
def fetch_url_content(url: str) -> dict[str, int | str]:
    """
    Fetch the content of a URL using a headless browser to handle JavaScript-rendered content.

    Args:
        url: The URL to fetch the content of.

    Returns:
        dict[str, int|str]: A dictionary containing the status code, content of the URL, and any error messages.
    """
    return _fetch_url_content_impl(url)


def _fetch_url_content_impl(url: str) -> dict[str, int | str]:
    """
    Internal implementation for fetching URL content.
    Not decorated with @tool so it can be called directly.
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
def summarize_for_logging_setup(page_content: str, focus_area: str = "logging and syslog configuration") -> dict[str, str]:
    """
    Uses an LLM to intelligently extract and summarize relevant information from vendor documentation.

    This tool uses AI to understand the context and extract only the information relevant to
    setting up external logging, syslog configuration, or other specified focus areas.

    Args:
        page_content: The full text content from a fetched URL (can be large)
        focus_area: What to focus on (default: "logging and syslog configuration")

    Returns:
        dict containing:
        - summary: Concise summary of relevant content
        - setup_instructions: Extracted setup steps if found
        - configuration_details: Important configuration parameters
        - has_relevant_content: Boolean indicating if relevant content was found
    """

    try:
        # Truncate very long content to fit in context
        max_length = 40000
        content_to_analyze = page_content[:max_length]
        if len(page_content) > max_length:
            content_to_analyze += "\n\n... (content truncated for analysis)"

        chain = web_page_content_summarizer_prompt | flash_llm | StrOutputParser()

        result_text = chain.invoke(
            {"content_to_analyze": content_to_analyze, "focus_area": focus_area}
        )

        # Parse the response
        has_relevant = "RELEVANT: Yes" in result_text or "RELEVANT: yes" in result_text

        # Extract sections
        summary = ""
        setup_instructions = ""
        config_details = ""

        if "SUMMARY:" in result_text:
            parts = result_text.split("SUMMARY:")
            if len(parts) > 1:
                summary_section = parts[1].split(
                    "SETUP_INSTRUCTIONS:")[0].strip()
                summary = summary_section

        if "SETUP_INSTRUCTIONS:" in result_text:
            parts = result_text.split("SETUP_INSTRUCTIONS:")
            if len(parts) > 1:
                setup_section = parts[1].split(
                    "CONFIGURATION_DETAILS:")[0].strip()
                setup_instructions = setup_section

        if "CONFIGURATION_DETAILS:" in result_text:
            parts = result_text.split("CONFIGURATION_DETAILS:")
            if len(parts) > 1:
                config_details = parts[1].strip()

        return {
            "has_relevant_content": has_relevant,
            "summary": summary if summary else "No summary available",
            "setup_instructions": setup_instructions if setup_instructions else "None found",
            "configuration_details": config_details if config_details else "None found",
            "full_response": result_text
        }

    except (ValueError, AttributeError, TypeError) as e:
        return {
            "has_relevant_content": False,
            "summary": f"Error analyzing content: {str(e)}",
            "setup_instructions": "Error during analysis",
            "configuration_details": "Error during analysis",
            "full_response": ""
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
    return _extract_url_context_impl(markdown_content, url)


def _extract_url_context_impl(markdown_content: str, url: str) -> dict[str, str]:
    """
    Internal implementation for extracting URL context.
    Not decorated with @tool so it can be called directly.
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


def extract_urls_from_markdown(markdown_content: str) -> list[str]:
    """
    Extract all URLs from markdown content.

    Args:
        markdown_content: The markdown content to extract URLs from.

    Returns:
        list[str]: List of unique URLs found in the content.
    """
    # Pattern to match markdown links [text](url) and bare URLs
    markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    bare_url_pattern = r'https?://[^\s\)]+'

    urls = set()

    # Extract markdown links
    markdown_links: list[str] = re.findall(markdown_link_pattern, markdown_content)
    for _, url in markdown_links:
        if url.startswith(('http', 'https')):
            urls.add(url.strip())

    # Extract bare URLs (not already captured in markdown links)
    bare_urls: list[str] = re.findall(bare_url_pattern, markdown_content)
    for url in bare_urls:
        # Only add if not already in markdown link format
        if url not in [link for _, link in markdown_links]:
            urls.add(url.strip())

    return list(urls)


def evaluate_single_url(url: str, markdown_content: str, integration_name: str, llm: Any) -> dict[str, Any]:
    """
    Evaluate a single URL to determine if it should be kept or removed.
    This function is designed to be called in parallel.

    Args:
        url: The URL to evaluate.
        markdown_content: The full markdown content.
        integration_name: The name of the integration.
        llm: The language model to use for evaluation.

    Returns:
        dict with 'url', 'should_remove', 'reason', 'status_code', 'section_type'
    """
    # Extract context
    context_info = _extract_url_context_impl(markdown_content, url)
    section_type = context_info.get('section_type', 'other')
    section = context_info.get('section', 'Unknown')

    # Fetch URL content (sync version for now, we'll call this from async wrapper)
    url_info = _fetch_url_content_impl(url)
    status_code = url_info.get('status_code', 0)
    content = url_info.get('content', '')

    # Determine if URL should be removed based on validation rules
    should_remove = False
    reason = ""

    # Rule 1: Always remove if status is not 200
    if status_code != 200:
        should_remove = True
        reason = f"Status code {status_code} (not 200)"
    # Rule 2: Always keep elastic.co if status is 200
    elif 'elastic.co' in url:
        should_remove = False
        reason = "elastic.co domain with status 200"
    # Rule 3: Section-specific validation
    else:
        # Use LLM to evaluate content relevance
        evaluation_prompt = f"""
        Evaluate if this URL should be kept in the {section} section.
        
        Product: {integration_name}
        Section: {section} (Type: {section_type})
        URL: {url}
        Status: {status_code}
        
        Content preview (first 1000 chars):
        {content[:1000]}
        
        Validation criteria for {section_type}:
        - product_info: Content should be about the product (general info, features, overview)
        - setup: Content MUST contain logging/syslog setup instructions
        - documentation: Content should be documentation/reference material
        - troubleshooting: Content should have troubleshooting information
        - other: Content should be relevant to the section
        
        Should this URL be kept? Answer with KEEP or REMOVE followed by a brief reason.
        """

        try:
            response = llm.invoke(
                [{"role": "user", "content": evaluation_prompt}])
            answer = response.content.strip().upper()

            if answer.startswith('REMOVE'):
                should_remove = True
                reason = answer.replace('REMOVE', '').strip(' :-')
            else:
                should_remove = False
                reason = answer.replace('KEEP', '').strip(' :-')
        except (RuntimeError, ValueError, AttributeError) as e:
            # If LLM fails, use conservative approach - keep the URL
            should_remove = False
            reason = f"LLM evaluation failed: {str(e)}, kept by default"

    return {
        "url": url,
        "should_remove": should_remove,
        "reason": reason,
        "status_code": status_code,
        "section_type": section_type,
        "section": section
    }


def evaluate_urls_parallel(urls: list[str], markdown_content: str, integration_name: str, llm: Any, max_concurrent: int = 5) -> list[dict[str, Any]]:
    """
    Evaluate multiple URLs in parallel using LangChain's batch execution.

    Args:
        urls: List of URLs to evaluate.
        markdown_content: The full markdown content.
        integration_name: The name of the integration.
        llm: The language model to use for evaluation.
        max_concurrent: Maximum number of concurrent evaluations.

    Returns:
        List of evaluation results for each URL.
    """
    if not urls:
        return []

    # Create a partial function with fixed parameters
    evaluate_fn = partial(
        evaluate_single_url,
        markdown_content=markdown_content,
        integration_name=integration_name,
        llm=llm
    )

    # Wrap in RunnableLambda for LangChain's parallel execution
    url_evaluator = RunnableLambda(evaluate_fn)

    # Use LangChain's batch() with max_concurrency for parallel execution
    # This handles threading/parallelism internally
    results = url_evaluator.batch(
        urls,
        config={"max_concurrency": max_concurrent}
    )

    # Filter out any failed results
    valid_results = []
    for result in results:
        if isinstance(result, dict) and "url" in result:
            valid_results.append(result)
        elif isinstance(result, Exception):
            print(f"Error evaluating URL: {result}")

    return valid_results
