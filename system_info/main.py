# pylint: disable=C0114,C0116

import os
import re
import sys
import json
import yaml

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from requests_html import HTMLSession

from templates import (
    setup_steps_prompt,
    service_info_prompt,
    link_verification_prompt,
)

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
)


def get_manifest(integration_name: str) -> dict:
    integration_path = os.environ.get("INTEGRATION_ROOT_PATH")
    if integration_path is None:
        raise ValueError("INTEGRATION_ROOT_PATH is not set")

    with open(
            f"{integration_path}/packages/{integration_name}/manifest.yml",
            "r",
            encoding="utf-8",
    ) as f:
        manifest = yaml.safe_load(f)
        if manifest is None:
            return ""

        return manifest


def generate_service_info(integration_name: str, manifest: dict) -> None:
    # Chain responsible for generating the setup steps
    setup_chain = setup_steps_prompt | llm | StrOutputParser()
    link_verification_chain = link_verification_prompt | llm | StrOutputParser()

    inputs = set()
    for policy_template in manifest["policy_templates"]:
        for inp in policy_template["inputs"]:
            inputs.add(inp["type"])

    # combined chain responsible for generating the service_info.md file
    chain = (
        {
            "integration_name": lambda x: x["integration_name"],
            "collection_via": lambda x: x["collection_via"],
            "setup_steps": setup_chain,
            "manifest": lambda x: x["manifest"]
        }
        | service_info_prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(validate_and_clean_urls)
    )

    print("Invoking chains...")
    result = chain.invoke({
        "integration_name": integration_name,
        "collection_via": inputs,
        "manifest": json.dumps(manifest)
    })

    print("Writing service info to file...")
    with open(
            f"service_info-{integration_name}.md", "w",
            encoding="utf-8") as f:
        f.write(result)


def validate_and_clean_urls(text: str) -> str:
    print("Verifying links...")
    link_verification_chain = link_verification_prompt | llm | StrOutputParser()
    
    # Find all markdown links: [text](url)
    urls = re.findall(r'https?://[^\s\)\]>]+', text)
    invalid_urls = set()
    
    for link in urls:
        # Clean the link of any trailing punctuation that might have been captured
        print(f"Verifying link: {link}")
        try:
            session = HTMLSession()
            response = session.get(link, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                print(f"Failed to get page content for {link} (Status: {response.status_code})")
                invalid_urls.add(link)
                continue

            soup = BeautifulSoup(response.html.text, 'html.parser')
            page_content = soup.get_text()

            verification = link_verification_chain.invoke({
                "link": link,
                "page_content": page_content,
            })

            print(f"Verification: {verification}")

            if "invalid" in verification.lower():
                invalid_urls.add(link)
        except Exception as e:
             print(f"Error verifying {link}: {e}")
             invalid_urls.add(link)

    if not invalid_urls:
        return text

    print(f"Removing invalid links: {', '.join(invalid_urls)}")
    
    cleaned_text = text
    for url in invalid_urls:
        escaped_url = re.escape(url)
        
        # Strategy 1: Standalone links (on their own line or in a list item)
        # Matches: Start of line, optional whitespace, optional bullet, optional whitespace, [text](url), optional whitespace, end of line
        # We also match the newline to remove the empty line
        pattern_standalone = r'(?m)^\s*[-*]?\s*\[[^\]]+\]\(' + escaped_url + r'\)\s*\n?'
        cleaned_text = re.sub(pattern_standalone, '', cleaned_text)
        
        # Strategy 2: Inline links
        # Matches: [text](url) -> replace with text
        pattern_inline = r'\[([^\]]+)\]\(' + escaped_url + r'\)'
        cleaned_text = re.sub(pattern_inline, r'\1', cleaned_text)
        
    return cleaned_text


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: python main.py <integration_name>")
        sys.exit(1)

    manifest = get_manifest(args[0].lower())
    if manifest is None:
        print(f"Manifest for {args[0].lower()} not found")
        sys.exit(1)

    generate_service_info(args[0].lower(), manifest)


if __name__ == "__main__":
    main()
