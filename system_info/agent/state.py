# pylint: disable=C0114,C0116
# flake8: noqa: E501

from typing import Annotated, TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


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
    product_documentation_urls: Annotated[list[str],
                                          "Product documentation URLs"]
    # Setup steps
    setup_steps: Annotated[list[str], "Setup steps"]
    verified_setup_steps: Annotated[list[str], "Verified setup steps"]

    # URLs
    verified_urls: Annotated[list[str], "Verified product documentation URLs"]
