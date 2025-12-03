# pylint: disable=C0114,C0116
# flake8: noqa: E501

import os
import re
import requests

from bs4 import BeautifulSoup
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.prompt import PromptTemplate

from .logger import logger
from .constants import DEBUG, LLM


integration_path = os.environ.get("INTEGRATION_ROOT_PATH")
if integration_path is None:
    raise ValueError("INTEGRATION_ROOT_PATH is not set")


web_search = DuckDuckGoSearchResults(
    verbose=DEBUG,
    output_format="json"
)


@tool
def list_integrations() -> str:
    """
    List all the available integration names with manifest files.
    Use this before doing a web search to list all the available integrations when the integration name is not found.

    Return the list of integration names in a newline separated string.
    """

    logger.info(
        "[TOOL] [list_integrations] Listing available integrations in the integration root path")
    integrations = os.listdir(f"{integration_path}/packages")
    logger.info("[TOOL] [list_integrations] Found %s integrations",
                len(integrations))
    return "\n".join(integrations) if integrations else ""


link_verification_prompt = PromptTemplate(
    input_variables=["link"],
    template="""
    You are a link verifier.
    You will be given a link and you need to verify if it is a valid link and has content.
    In the content from the page is missing, consider the page as invalid.

    If it is a valid link with content, you respond with "valid".
    If it is not a valid link, you respond with "invalid".

    Only respond with "valid" or "invalid"
    If the link is invalid, provide a reason for the invalidity.
    The reason should be a short description of the issue in 10 words or less.

    Link: {link}
    Page Content: {page_content}
    Answer:
    """
)


def verify_link(
    link: str
) -> tuple[str, bool]:
    print(f"Verifying link: {link}")
    try:
        response = requests.get(link, timeout=10, allow_redirects=True)
        if response.status != 200:
            print(
                f"Failed to get page content for {link} (Status: {response.status})")
            return link, False

        text = response.text()
        soup = BeautifulSoup(text, 'html.parser')
        page_content = soup.get_text()

        chain = link_verification_prompt | LLM | StrOutputParser()
        verification = chain.invoke({
            "link": link,
            "page_content": page_content,
        })

        print(f"Verification: {verification}")

        if "invalid" in verification.lower():
            return link, False

        return link, True
    except Exception as e:
        print(f"Error verifying {link}: {e}")
        return link, False


def validate_urls(text: str) -> set[str]:
    print("Verifying links...")

    # Find all markdown links: [text](url)
    urls = re.findall(r'https?://[^\s\)\]>]+', text)
    if not urls:
        return set()

    invalid_urls = set()

    for link in urls:
        is_valid = verify_link(link)
        if not is_valid:
            invalid_urls.add(link)

    return invalid_urls


def clean_result_text(text: str, invalid_urls: set[str]) -> str:
    """
    Clean the text by removing the invalid links.
    """
    print(f"Removing invalid links: {', '.join(invalid_urls)}")

    cleaned_text = text
    for url in invalid_urls:
        escaped_url = re.escape(url)

        # Strategy 1: Standalone links (on their own line or in a list item)
        # Matches: Start of line, optional whitespace, optional bullet, optional
        # whitespace, [text](url), optional whitespace, end of line
        # We also match the newline to remove the empty line
        pattern_standalone = r'(?m)^\s*[-*]?\s*\[[^\]]+\]\(' + \
            escaped_url + r'\)\s*\n?'
        cleaned_text = re.sub(pattern_standalone, '', cleaned_text)

        # Strategy 2: Inline links
        # Matches: [text](url) -> replace with text
        pattern_inline = r'\[([^\]]+)\]\(' + escaped_url + r'\)'
        cleaned_text = re.sub(pattern_inline, r'\1', cleaned_text)

    return cleaned_text
