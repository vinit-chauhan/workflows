import os
import yaml
from typing import Any, Literal

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
    if answer in packages:
        return {"integration_name": answer}
    else:
        return {"integration_name": ""}


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

    with open(manifest_path, "r", encoding="utf-8") as f:
        try:
            integration_manifest = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error loading manifest: {e}")
            integration_manifest = {}

    with open(docs_path, "r", encoding="utf-8") as f:
        integration_docs = f.read()

    return {"integration_manifest": integration_manifest, "integration_docs": integration_docs}


def find_product_setup_instructions_node(_: WorkflowState) -> dict[str, Any]:
    """
    Find the product setup instructions for the product.
    """
    return {"product_setup_instructions": ""}


def is_existing_integration(state: WorkflowState) -> Literal["yes", "no"]:
    """
    Check if the package info should be added to the state.
    """

    integration_name = state["integration_name"]
    if not integration_name:
        return "no"

    return "yes"
