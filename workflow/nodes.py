import os
from typing import Any, Literal

import yaml
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from .state import WorkflowState
from .constants import flash_llm, INTEGRATION_ROOT_PATH
from .agents import (
    final_result_generation_agent,
    setup_instructions_external_info_agent,
    search_relevant_package_agent,
    setup_instructions_context_agent,
)
from .prompts import (
    setup_instructions_external_info_prompt,
    search_relevant_package_prompt,
    setup_instructions_context_prompt,
    final_result_generation_prompt,
    find_relevant_package_prompt,
    FIND_RELEVANT_PACKAGE_SYSTEM_PROMPT,
)
from .utils import (
    extract_urls_from_markdown,
    evaluate_urls_parallel,
)


def find_relevant_packages_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the most relevant packages for the user's input.
    """
    user_input = state["messages"][-1].content

    try:
        packages_path = os.path.join(INTEGRATION_ROOT_PATH, "packages")
        packages = os.listdir(packages_path)
    except FileNotFoundError:
        return {"user_input": user_input, "integration_name": ""}

    # Use the proper prompt template
    prompt = find_relevant_package_prompt.invoke({
        "user_input": user_input,
        "packages": ", ".join(packages)
    }).to_string()

    # Create messages with system prompt
    messages = [
        {"role": "system", "content": FIND_RELEVANT_PACKAGE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    response = (flash_llm | StrOutputParser()).invoke(messages)
    answer = response.strip()

    # If the answer is in the packages, return the integration name
    # Otherwise, return an empty string
    answer = answer if answer in packages else ""
    return {"user_input": user_input, "integration_name": answer}


def get_package_info_node(state: WorkflowState) -> dict[str, Any]:
    """
    Get More information about the integration package.
    """

    integration_name = state["integration_name"]
    if not integration_name:
        return {"integration_manifest": {}, "integration_docs": ""}

    package_path = os.path.join(
        INTEGRATION_ROOT_PATH, "packages", integration_name)
    manifest_path = os.path.join(package_path, "manifest.yml")
    docs_path = os.path.join(package_path, "_dev",
                             "build", "docs", "README.md")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                integration_manifest = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error loading manifest: {e}")
                integration_manifest = {}

        with open(docs_path, "r", encoding="utf-8") as f:
            integration_docs = f.read()
    except FileNotFoundError as e:
        print(f"Error loading manifest or docs: {e}")
        return {"integration_manifest": {}, "integration_docs": ""}

    return {"integration_manifest": integration_manifest, "integration_docs": integration_docs}


def setup_instructions_context_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the relevant product setup instructions for the product from the integration docs.
    """
    integration_name = state["integration_name"]
    integration_docs = state["integration_docs"]
    integration_manifest = state["integration_manifest"]

    prompt = setup_instructions_context_prompt.invoke({
        "integration_name": integration_name,
        "integration_docs": integration_docs,
        "integration_manifest": integration_manifest
    }).to_string()

    response = setup_instructions_context_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )

    message: AIMessage = response["messages"][-1]
    return {"integration_context": message.text.strip('`')}


def setup_instructions_external_info_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the product setup instructions from internet for the product.
    """

    product_name = state["integration_name"]
    integration_context = state["integration_context"]

    prompt = setup_instructions_external_info_prompt.invoke({
        "integration_name": product_name,
        "integration_context": integration_context if integration_context else ""
    }).to_string()

    response = setup_instructions_external_info_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )

    message: AIMessage = response["messages"][-1]
    return {"product_setup_instructions": message.text.strip('`')}


def search_relevant_package_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the relevant package for the product.
    """
    user_input = state["user_input"]

    print("[Experimental] Searching for relevant package for the product...")

    prompt = search_relevant_package_prompt.invoke({
        "user_input": user_input
    }).to_string()

    response = search_relevant_package_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )

    message: AIMessage = response["messages"][-1]
    return {"integration_name": message.text.lower().strip()}


def is_existing_integration(state: WorkflowState) -> Literal["yes", "no"]:
    """
    Check if the package info should be added to the state.
    """

    integration_name = state["integration_name"]
    if not integration_name:
        return "no"

    return "yes"


def final_result_generation_node(state: WorkflowState) -> dict[str, Any]:
    """
    Generate the final result.
    """

    prompt = final_result_generation_prompt.invoke({
        "integration_name": state["integration_name"],
        "integration_context": state["integration_context"],
        "integration_docs": state["integration_docs"],
        "product_setup_instructions": state["product_setup_instructions"],
    }).to_string()

    response = final_result_generation_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )

    message: AIMessage = response["messages"][-1]

    return {"final_result": message.text.strip('`')}


def extract_urls_node(state: WorkflowState) -> dict[str, Any]:
    """
    Extract all URLs from the final result programmatically.
    Step 1 of parallel URL verification.
    """
    final_result = state["final_result"]

    # Extract all URLs from markdown
    urls = extract_urls_from_markdown(final_result)

    return {"urls_to_verify": urls}


def url_evaluation_node(state: WorkflowState) -> dict[str, Any]:
    """
    Evaluate all URLs in parallel to determine which should be removed.
    Step 2 of parallel URL verification.
    Uses LangChain's batch() for parallel execution.
    """
    urls = state["urls_to_verify"]
    final_result = state["final_result"]
    integration_name = state["integration_name"]

    if not urls:
        return {"urls_to_remove": []}

    # Run parallel evaluation using LangChain's batch
    try:
        evaluation_results = evaluate_urls_parallel(
            urls=urls,
            markdown_content=final_result,
            integration_name=integration_name,
            llm=flash_llm,
            max_concurrent=5  # Limit concurrent browser instances
        )
    except (RuntimeError, OSError, ValueError) as e:
        print(f"[URL Verification] Error during parallel evaluation: {e}")
        return {"urls_to_remove": []}

    # Collect URLs that should be removed
    urls_to_remove = []

    for result in evaluation_results:
        url = result['url']
        should_remove = result['should_remove']

        if should_remove:
            urls_to_remove.append(url)

    return {"urls_to_remove": urls_to_remove}


def url_removal_node(state: WorkflowState) -> dict[str, Any]:
    """
    Remove marked URLs from the final result using LLM.
    Step 3 of parallel URL verification.
    """
    urls_to_remove = state["urls_to_remove"]
    final_result = state["final_result"]

    if not urls_to_remove:
        return {"final_result": final_result}

    # Create a prompt for the LLM to remove URLs
    removal_prompt = f"""
Remove the following URLs from the markdown document. Remove the entire line or markdown link containing each URL.
Preserve all other content and formatting exactly as it is.

URLs to remove:
{chr(10).join(f"- {url}" for url in urls_to_remove)}

Document:
```
{final_result}
```

Return the cleaned document with the specified URLs removed. Maintain all markdown formatting.

Answer:
"""

    try:
        response = flash_llm.invoke(
            [{"role": "user", "content": removal_prompt}])
        cleaned_result = response.content.strip('`').strip()

        return {"final_result": cleaned_result}
    except (RuntimeError, ValueError, AttributeError):
        # Return original result if removal fails
        return {"final_result": final_result}
