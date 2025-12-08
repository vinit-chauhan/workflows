import os
from typing import Any, Literal

import yaml
from langchain_core.messages import AIMessage, HumanMessage

from .state import WorkflowState
from .constants import flash_llm, INTEGRATION_ROOT_PATH
from .agents import (
    final_result_generation_agent,
    product_setup_external_agent,
    search_relevant_package_agent,
    setup_instructions_context_agent,
    url_verifier_agent,
)
from .prompts import (
    product_setup_external_prompt,
    search_relevant_package_prompt,
    setup_instructions_context_prompt,
    final_result_generation_prompt,
    url_verification_prompt,
)


def find_relevant_packages_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the most relevant packages for the user's input.
    """

    packages_path = os.path.join(INTEGRATION_ROOT_PATH, "packages")

    packages = os.listdir(packages_path)
    user_input = state["messages"][-1].content

    prompt = f"""You are a helpful assistant.
Your task is to find the most relevant packages for the user's input.
Return only the name of the package, no other text.

Example:
User input: "cisco_ios"
Packages: cisco_ios,cisco_duo,cisco_asa
Answer: cisco_ios


User input: {user_input}
Packages: {",".join(packages)}
"""
    response = flash_llm.invoke(prompt)
    answer = response.content.strip()

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

    prompt = product_setup_external_prompt.invoke({
        "integration_name": product_name,
        "integration_context": integration_context if integration_context else ""
    }).to_string()

    response = product_setup_external_agent.invoke(
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


def url_verification_node(state: WorkflowState) -> dict[str, Any]:
    """
    Verify the URLs in the final result.
    """

    final_result = state["final_result"]

    prompt = url_verification_prompt.invoke({
        "product_name": state["integration_name"],
        "final_result": final_result
    }).to_string()

    response = url_verifier_agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    message: AIMessage = response["messages"][-1]
    return {"final_result_verified": message.text.strip('`').strip(), "messages": response["messages"]}
