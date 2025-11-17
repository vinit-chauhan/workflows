# pylint: disable=C0114,C0116
# flake8: noqa: E501

import os
import requests
import yaml

from langchain.tools import tool

from .constants import LLM


integration_path = os.environ.get("INTEGRATION_ROOT_PATH")
if integration_path is None:
    raise ValueError("INTEGRATION_ROOT_PATH is not set")


@tool
def list_available_manifests() -> str:
    """
    List all the available manifests in the integration root path.
    """
    manifests = os.listdir(f"{integration_path}/packages")
    return "\n".join(manifests)


@tool
def read_manifest(integration_name: str) -> str:
    """
    Read the manifest.yml file for the given integration name.
    """
    with open(
            f"{integration_path}/packages/{integration_name}/manifest.yml",
            "r",
            encoding="utf-8",
    ) as f:
        manifest = yaml.safe_load(f)
        if manifest is None:
            return ""

        return manifest


@tool
def write_service_info(service_info: str) -> str:
    """
    Write the service info to the service_info.md file.
    """

    with open("service_info.md", "w", encoding="utf-8") as f:
        f.write(service_info)

    return "Service info written to service_info.md"


@tool
def verify_url(url: str) -> str:
    """
    Verify the URLs are valid and has good quality content.
    """

    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return False

    if response.text is None:
        return False

    content = response.text

    prompt = f"""
    You are a helpful assistant that verifies the URLs are valid and has good quality content.
    The content of the URL is:
    ```
    {content}
    ```

    Is the content of the URL good quality and valid? If yes, return "True". If no, return "False".
    Return only the boolean value, no other text or explanation.
    """

    response = LLM.invoke(prompt)
    return response.content
