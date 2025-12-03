# pylint: disable=C0114,C0116,W0613,W0703
import os
import yaml

from langchain_core.messages import (
    SystemMessage,
    AIMessage,
    HumanMessage,
)

from .constants import LLM, INTEGRATION_ROOT_PATH
from .tools import (
    list_integrations,
    validate_urls,
    clean_result_text,
    web_search,
)
from .prompts import SYSTEM_PROMPT
from .state import GenerationState
from .logger import logger

# ============================================================================
# SEQUENTIAL WORKFLOW NODES
# ============================================================================

def list_integrations_node(_: GenerationState) -> dict:
    """
    Step 1: List available integrations (optional validation step)
    """
    logger.info("[STEP 1] Listing integrations")
    result = list_integrations.invoke({})
    logger.info("[STEP 1] Found integrations: %d", str(result).count("\n"))
    return {"messages": [AIMessage(content=f"Available integrations: {result}")]}


def read_manifest_node(state: GenerationState) -> dict:
    """
    Step 2: Read the manifest file for the integration
    """
    integration_name = state["integration_name"]

    logger.info("[STEP 2] Reading manifest for integration: %s",
                integration_name)

    # Read manifest directly
    try:
        with open(
                f"{INTEGRATION_ROOT_PATH}/packages/{integration_name}/manifest.yml",
                "r",
                encoding="utf-8",
        ) as f:
            manifest_yaml = f.read()
            manifest_dict = yaml.safe_load(manifest_yaml)

            if manifest_dict:
                logger.info("[STEP 2] Manifest loaded successfully")

                # Also get data streams
                try:
                    data_streams_path = f"{INTEGRATION_ROOT_PATH}/packages/{integration_name}/data_stream"
                    data_streams = os.listdir(data_streams_path)
                    data_streams = [ds for ds in data_streams if ds]
                except Exception as e:
                    logger.warning(
                        "[STEP 2] Could not list data streams: %s", e)
                    data_streams = []

                return {
                    "manifest": manifest_dict,
                    "data_streams": data_streams,
                    "messages": [AIMessage(content=f"Manifest read successfully. Data streams: {data_streams}")]
                }
    except Exception as e:
        logger.error("[STEP 2] Error reading manifest: %s", e)

    return {"messages": [AIMessage(content="Manifest read but could not parse")]}


def web_search_node(state: GenerationState) -> dict:
    """
    Step 3: Perform web search for product logging setup instructions
    """
    logger.info("[STEP 3] Performing web search for integration setup")

    manifest = state.get("manifest", {})
    integration_name = state["integration_name"]
    product_name = manifest.get("title", integration_name)

    data_streams = state.get("data_streams", [])
    collection_method = state.get("collection_method", "")

    # Perform searches for setup instructions
    search_queries = [
        f"{product_name} external logging configuration setup guide for {",".join(data_streams)}",
        f"How to configure {product_name} to send logs to Elastic Agent",
        f"{product_name} external logging setup via {collection_method} for {",".join(data_streams)}",
    ]

    search_results = []
    for query in search_queries:
        logger.info("[STEP 3] Searching: %s", query)
        result = web_search.invoke({"query": query})
        search_results.append(result)

    combined_results = "\n\n---\n\n".join(search_results)

    return {
        "search_results": search_results,
        "messages": [AIMessage(content=f"Search results:\n{combined_results}")]
    }


def build_doc_node(state: GenerationState) -> dict:
    """
    Step 4: Build the documentation using LLM with all gathered information
    """
    logger.info("[STEP 4] Building documentation")

    integration_name = state["integration_name"]
    manifest = state.get("manifest", {})
    data_streams = state.get("data_streams", [])
    messages = state.get("messages", [])

    # Build context for the LLM
    context = f"""
You are creating setup documentation for the {integration_name} integration.

## Integration Information:
- Name: {manifest.get('name', integration_name)}
- Description: {manifest.get('description', 'N/A')}
- Type: {manifest.get('type', 'N/A')}
- Data Streams: {', '.join(data_streams)}

## Previous Search Results:
{messages[-1].content if messages else 'No search results available'}

## Your Task:
Generate complete setup documentation following this structure:

```
# Set Up Instructions

## Vendor prerequisites
[List what users need from the vendor side]

## Elastic prerequisites
[List Elastic Stack requirements - use version from manifest: {manifest.get('conditions', {}).get('kibana', {}).get('version', '^8.14.0')}]

## Vendor set up steps
[Detailed steps to configure the vendor system to send logs/data to Elastic Agent. Include specific commands or configuration examples where applicable.]

## Kibana set up steps
[Step-by-step guide to configure the integration in Kibana]

## Validation Steps
[How to verify the integration is working correctly]

# Troubleshooting

## Common Configuration Issues
[List common problems and solutions]

## Ingestion Errors
[How to handle data ingestion issues]

## API Authentication Errors
[If applicable, how to resolve authentication issues]

## Vendor Resources
[Links to vendor documentation - provide actual URLs where possible]

# Documentation sites
[List of relevant documentation URLs]
```

Generate the documentation now:
"""

    # Call LLM to generate documentation
    system_prompt = SystemMessage(content=SYSTEM_PROMPT)
    prompt = HumanMessage(content=context)
    response = LLM.invoke([system_prompt, prompt])

    doc_content = response.content if hasattr(
        response, 'content') else str(response)

    return {
        "service_info": doc_content,
        "messages": [AIMessage(content=doc_content)]
    }


def validate_urls_node(state: GenerationState) -> dict:
    """
    Step 5.1: Extract and validate URLs from the documentation
    """
    logger.info("[STEP 5.1] Validating URLs in documentation")

    service_info = state.get("service_info", "")

    invalid_urls = validate_urls(service_info)

    return {
        "invalid_urls": list(invalid_urls)
    }


def clean_service_info_node(state: GenerationState) -> dict:
    """
    Step 5.2: Clean the service info
    """
    logger.info("[STEP 5.2] Cleaning service info")

    service_info = state.get("service_info", "")
    invalid_urls = state.get("invalid_urls", [])
    cleaned_service_info = clean_result_text(service_info, invalid_urls)

    return {
        "service_info": cleaned_service_info
    }


def write_response_node(state: GenerationState) -> dict:
    """
    Step 6: Write the final documentation to file
    """
    logger.info("[STEP 6] Writing final documentation to file")

    print("setup_steps", state.get("setup_steps", ""))

    service_info = state.get("service_info", "")
    integration_name = state.get("integration_name", "")
    filename = f"service_info-{integration_name.lower()}.md"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(service_info)
        logger.info(
            "[STEP 6] Successfully wrote documentation to %s", filename)
        return {
            "messages": [AIMessage(content=f"Documentation written to {filename}")]
        }
    except (IOError, OSError) as e:
        logger.error("[STEP 6] Error writing to file: %s", e)
        return {
            "messages": [AIMessage(content=f"Error writing file: {e}")]
        }
