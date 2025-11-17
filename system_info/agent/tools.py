# pylint: disable=C0114,C0116
# flake8: noqa: E501

import os
import requests
import yaml

from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from .logger import logger
from .constants import LLM, DEBUG


integration_path = os.environ.get("INTEGRATION_ROOT_PATH")
if integration_path is None:
    raise ValueError("INTEGRATION_ROOT_PATH is not set")


web_search = DuckDuckGoSearchRun(
    verbose=DEBUG,
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
    return "\n".join(integrations) if integrations else "No integrations found"


@tool
def read_manifest(integration_name: str) -> str:
    """
    Read the manifest.yml file for the given integration name.

    Manifest file has the following data:
    - name: Name of the integration
    - input_types: List of input types (collection methods) supported by the integration
    - additional_info: Additional information about the integration

    Return the manifest data in a yaml format.
    """

    logger.info(
        "[TOOL] [read_manifest] Reading manifest for the integration: %s", integration_name)
    try:
        with open(
                f"{integration_path}/packages/{integration_name}/manifest.yml",
                "r",
                encoding="utf-8",
        ) as f:
            manifest = yaml.safe_load(f)
            if manifest is None:
                return ""

            return manifest
    except Exception as e:
        logger.error(
            "[TOOL] [read_manifest] Error reading manifest for the integration: %s: %s", integration_name, e)
        return ""


@tool
def list_data_streams(integration_name: str) -> str:
    """
    List all the data streams for the given integration name.

    Return the list of data streams in a newline separated string.
    """
    logger.info("[TOOL] [list_data_streams] Listing data streams for the integration: %s",
                integration_name)

    try:
        data_streams = os.listdir(
            f"{integration_path}/packages/{integration_name}/data_stream")
        logger.info("[TOOL] [list_data_streams] Found %s data streams",
                    len(data_streams))
        return "\n".join(data_streams) if data_streams else "No data streams found"
    except Exception as e:
        logger.error(
            "[TOOL] [list_data_streams] Error listing data streams for the integration %s: %s",
            integration_name, e)
        return f"Error: Could not list data streams for {integration_name}"


@tool
def write_service_info(service_info: str) -> str:
    """
    Write the service info to the service_info.md file.
    """
    logger.info(
        "[TOOL] [write_service_info] Writing service info to service_info.md")
    try:
        with open("service_info.md", "w", encoding="utf-8") as f:
            f.write(service_info)
        return "Service info written to service_info.md"
    except Exception as e:
        logger.error(
            "[TOOL] [write_service_info] Error writing service info to service_info.md: %s", e)
        return "Error writing service info to service_info.md"


@tool
def verify_url(url: str) -> str:
    """
    Verify the URLs are valid and has good quality content.

    Return the boolean value, no other text or explanation.
    """

    logger.info("[TOOL] [verify_url] Verifying URL: %s", url)
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        return False

    if response.text is None:
        return False

    content = response.text

    logger.debug("[TOOL] [verify_url] Fetched content of the URL: %s", url)

    prompt = f"""
    You are a helpful assistant that verifies the URLs are valid and has good quality content.

    The content of url for product X is good quality if it answers the question the following question: 
    "How to setup external logging in context of the product X?"
    
    The content of the URL is:
    ```
    {content}
    ```

    Is the content of the URL good quality and valid? If yes, return "True". If no, return "False".
    Return only the boolean value, no other text or explanation.

    Example with Reasoning for your understanding:
    
    Example:
    url: https://www.cisco.com
    Answer: True
    Reason: The content of the URL is a good quality and valid.

    url: https://www.cisco.com/c/en/us/td/docs/security/firepower/70/fdm/fptd-fdm-config-guide-700/fptd-fdm-logging.html
    Answer: False
    Reason: URL is valid but the there's no good quality content. The page shows "content not found".
    """

    response = LLM.invoke(
        prompt, config={
            "verbose": DEBUG,
        }
    )

    logger.debug("[TOOL] [verify_url] URL Evaluation Result: %s",
                 response.content)
    return response.content
