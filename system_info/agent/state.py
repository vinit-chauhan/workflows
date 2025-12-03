# pylint: disable=C0114,C0116
# flake8: noqa: E501

from operator import add
from typing import Annotated, TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)


class GenerationState(TypedDict):
    """
    State for the generation of the service info.
    """
    # Messages for the agent
    messages: Annotated[list[BaseMessage], add_messages]

    # Response from the agent
    service_info: Annotated[str, "Content of the service info file"]

    # Information about the integration
    manifest: Annotated[dict, "Data from the manifest file"]
    integration_name: Annotated[str,
                                "Name of the integration that the user the provided"]
    collection_method: Annotated[str,
                                 "Collection method (tcp, udp, api, logfile)"]
    data_streams: Annotated[list[str], "Data streams"]
    search_results: Annotated[list[dict],
                              "Search results from the web search tool", add]
    # Setup steps
    setup_steps: Annotated[list[str], "Setup steps"]
    verified_setup_steps: Annotated[list[str], "Verified setup steps"]

    # URLs
    invalid_urls: Annotated[list[str], "List of invalid URLs to be removed from the service info", add]


def default_state(integration_name: str) -> GenerationState:
    return GenerationState({
        "integration_name": integration_name,
        "messages": [
            HumanMessage(
                content="Generate system documentation for the integration.")
        ],
        "service_info": "",
        "manifest": {},
        "collection_method": "",
        "data_streams": [],
        "product_documentation_urls": [],
        "setup_steps": [],
        "verified_setup_steps": [],
        "verified_urls": [],
    })
