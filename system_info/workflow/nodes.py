import os
from typing import Any, Literal

import yaml
from langchain_core.messages import AIMessage, HumanMessage

from .agents import product_setup_agent, find_relevant_package_agent, find_relevant_package_prompt
from .prompts import product_setup_prompt
from .state import WorkflowState
from .constants import flash_llm, INTEGRATION_ROOT_PATH


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


def setup_instructions_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the product setup instructions for the product.
    """

    product_name = state["integration_name"]

    prompt = product_setup_prompt.invoke({
        "integration_name": product_name
    }).to_string()

    response = product_setup_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )

    message: AIMessage = response["messages"][-1]
    return {"product_setup_instructions": message.text.strip('`')}


def find_relevant_package_node(state: WorkflowState) -> dict[str, Any]:
    """
    Find the relevant package for the product.
    """
    user_input = state["user_input"]

    prompt = find_relevant_package_prompt.invoke({
        "user_input": user_input
    }).to_string()

    response = find_relevant_package_agent.invoke(
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
