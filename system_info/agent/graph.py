import os
from typing import Literal
from langgraph.graph import StateGraph, END

from .state import GenerationState
from .logger import logger
from .constants import INTEGRATION_ROOT_PATH, DEBUG
from .agent import (
    list_integrations_node,
    read_manifest_node,
    web_search_node,
    build_doc_node,
    validate_urls_node,
    clean_service_info_node,
    write_response_node,
)

# ============================================================================
# graph GRAPH CONSTRUCTION
# ============================================================================


def should_search_package(state: GenerationState) -> Literal["list_integrations", "read_manifest"]:
    """
    If the package is not found in the integration path, return "list_integrations"
    If the package is found in the integration path, return "read_manifest"
    """
    integration_name = state["integration_name"]
    package_path = f"{INTEGRATION_ROOT_PATH}/packages/{integration_name}"
    if os.path.exists(package_path):
        return "read_manifest"
    else:
        return "list_integrations"


def should_search_again(state: GenerationState) -> Literal["web_search", "validate_urls"]:
    """
    Conditional edge: Decide if we need more web searches
    """
    service_info = state.get("service_info", "")
    messages = state.get("messages", [])

    # Simple heuristic: if documentation is too short or doesn't have URLs, search again
    # Limit to maximum 2 iterations
    search_count = sum(
        1 for msg in messages if "Search results:" in str(msg.content))

    if search_count < 2 and len(service_info) < 500:
        logger.info(
            "[DECISION] Documentation too short, performing another search")
        return "web_search"

    logger.info("[DECISION] Moving to URL validation")
    return "validate_urls"


# Create the StateGraph with sequential flow
graph = StateGraph(GenerationState)

# Add all nodes in sequence
graph.add_node("list_integrations", list_integrations_node)
graph.add_node("read_manifest", read_manifest_node)
graph.add_node("web_search", web_search_node)
graph.add_node("build_doc", build_doc_node)
graph.add_node("validate_urls", validate_urls_node)
graph.add_node("clean_service_info", clean_service_info_node)
graph.add_node("write_response", write_response_node)

# Set entry point
graph.set_entry_point("read_manifest")

# Create the sequential flow
graph.add_edge("read_manifest", "web_search")
graph.add_edge("web_search", "build_doc")

# TODO: Add conditional edge to check if the package exists in the integration path
# graph.add_conditional_edges(
#     "read_manifest",
#     should_search_package,
#     {
#         "list_integrations": "list_integrations",
#         "read_manifest": "read_manifest",
#     }
# )

# Conditional edge: decide if we need more searches or move to validation
graph.add_conditional_edges(
    "build_doc",
    should_search_again,
    {
        "web_search": "web_search",  # Loop back for more searches
        "validate_urls": "validate_urls",  # Move forward to validation
    }
)

graph.add_edge("validate_urls", "clean_service_info")
graph.add_edge("clean_service_info", "write_response")
graph.add_edge("write_response", END)


# Compile the graph
workflow = graph.compile(debug=DEBUG)
