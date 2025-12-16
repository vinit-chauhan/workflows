from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from langchain_core.output_parsers import StrOutputParser

from .prompts import web_page_content_summarizer_prompt
from .constants import DEBUG, flash_llm
from .utils import fetch_url_content

web_search_tool = DuckDuckGoSearchResults(max_results=10, verbose=DEBUG)


@tool
def fetch_url_content_tool(url: str) -> dict[str, int | str]:
    """
    Fetch the content of a URL using a headless browser to handle JavaScript-rendered content.

    Args:
        url: The URL to fetch the content of.

    Returns:
        dict[str, int|str]: A dictionary containing the status code, content of the URL, and any error messages.
    """
    return fetch_url_content(url)


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
