from operator import add
from typing import Annotated, TypedDict

from langgraph.graph.message import AnyMessage, add_messages


class WorkflowState(TypedDict):
    """
    The state for the workflow.
    """
    messages: Annotated[AnyMessage, add_messages]

    user_input: Annotated[str, "The user's input"]
    integration_name: Annotated[str, "The name of the integration package"]
    integration_manifest: Annotated[dict,
                                    "The manifest of the integration package"]
    integration_docs: Annotated[str, "The docs of the integration package"]

    integration_context: Annotated[str, "The context of the integration"]

    product_setup_instructions: Annotated[str,
                                          "The setup instructions for the product"]

    final_result: Annotated[str, "The final result for the product"]
    
    urls_to_verify: Annotated[list[str], "List of URLs extracted from final result", add]
    urls_to_remove: Annotated[list[str], "List of URLs that should be removed", add]


def default_state() -> 'WorkflowState':
    """
    Returns the default state for the workflow.
    """
    return {
        "messages": [],
        "integration_name": "",
        "integration_manifest": {},
        "integration_docs": "",
        "integration_context": "",
        "product_setup_instructions": "",
        "final_result": "",
        "urls_to_verify": [],
        "urls_to_remove": [],
    }
