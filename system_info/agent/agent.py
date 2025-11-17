# pylint: disable=C0114,C0116
from typing import List, Literal
from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .constants import LLM, DEBUG
from .tools import (
    read_manifest,
    write_service_info,
    list_integrations,
    list_data_streams,
    web_search,
)
from .prompts import SYSTEM_PROMPT
from .state import GenerationState
from .logger import logger

tools: List[BaseTool] = [
    read_manifest,
    write_service_info,
    list_integrations,
    list_data_streams,
    web_search,
]

# Bind tools to the LLM
llm_with_tools = LLM.bind_tools(
    tools,
    tool_config={
        "temperature": 0.0,
    }
)


def call_agent(state: GenerationState) -> dict:
    """
    Agent node that calls the LLM with tools.
    Injects state context into the system prompt so the LLM can access it.
    """
    messages = state.get("messages", [])
    integration_name = state.get("integration_name", "")
    data_streams = state.get("data_streams", [])
    verified_urls = state.get("verified_urls", [])

    # Add system prompt with state context if it's the first message
    if len(messages) == 1 or not any(
            isinstance(msg, SystemMessage) for msg in messages):
        # Inject state information into the system prompt
        context = "\n\n## Current Context\n"
        context += f"- Integration name provided by user: {integration_name}\n"

        if data_streams:
            ds_list = ', '.join(data_streams)
            context += f"- Data streams discovered: {ds_list}\n"

        if verified_urls:
            context += f"- Verified URLs found: {len(verified_urls)}\n"

        enhanced_prompt = SYSTEM_PROMPT + context
        messages = [SystemMessage(content=enhanced_prompt)] + messages

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def process_tool_results(state: GenerationState) -> dict:
    """
    Post-process tool results and update state fields.
    This node extracts structured data from tool outputs and stores in state.
    """
    messages = state.get("messages", [])
    updates = {}

    # Find the most recent tool messages
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_name = msg.name

            # Extract data streams from list_data_streams tool
            if tool_name == "list_data_streams" and msg.content:
                if not msg.content.startswith("Error"):
                    data_streams = [
                        ds.strip() for ds in msg.content.split('\n')
                        if ds.strip()
                    ]
                    if data_streams:
                        updates["data_streams"] = data_streams
                        logger.info(
                            "[PROCESS] Updated state with %d data streams",
                            len(data_streams))

            # Extract manifest from read_manifest tool
            elif tool_name == "read_manifest" and msg.content:
                try:
                    import json
                    manifest = json.loads(msg.content)
                    if manifest:
                        updates["manifest"] = manifest
                        logger.info("[PROCESS] Updated state with manifest")
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    logger.debug("[PROCESS] Failed to parse manifest: %s", e)

            # Track verified URLs from verify_url tool
            elif tool_name == "verify_url" and "True" in str(msg.content):
                verified_urls = state.get("verified_urls", [])
                # Extract URL from previous messages if possible
                # For now, just increment count
                if "verified_urls" not in updates:
                    updates["verified_urls"] = verified_urls
                logger.info("[PROCESS] URL verified successfully")

    return updates


def should_continue(state: GenerationState) -> Literal["tools", END]:
    """
    Determines whether to continue with tool calls, process results, or end.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    # If there are tool calls, continue to the tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end the graph
    return END


def should_process(state: GenerationState) -> Literal["agent", "process"]:
    """
    After tools run, decide if we need to process results.
    """
    messages = state.get("messages", [])

    # Check if the last few messages include tool results
    recent_tools = [
        msg for msg in messages[-5:]
        if isinstance(msg, ToolMessage)
    ]

    if recent_tools:
        return "process"
    return "agent"


def finalize_state(state: GenerationState) -> dict:
    """
    Final processing before ending - ensure state is complete.
    Extract URLs from generated markdown, verify them, and write to file.
    """
    import re
    import requests

    logger.info("[FINALIZE] Completing state processing")

    # Extract any final information from the last message
    messages = state.get("messages", [])
    service_info_content = ""
    filename = f"service_info-{state.get('integration_name', '').lower()}s.md"

    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            content = last_message.content
            if isinstance(content, list):
                # Extract text from content blocks
                text_content = "".join([
                    item.get("text", "") if isinstance(item, dict)
                    else str(item)
                    for item in content
                ])
                service_info_content = text_content
            elif isinstance(content, str):
                service_info_content = content

    # Write to file if we have content and it looks like documentation
    if (service_info_content and
            "# Set Up Instructions" in service_info_content):

        # Extract URLs from markdown
        url_pattern = r'https?://[^\s\)\]>]+'
        urls = re.findall(url_pattern, service_info_content)
        verified_urls = []
        invalid_urls = []

        logger.info("[FINALIZE] Found %d URLs to verify", len(urls))

        # Verify each URL
        for url in set(urls):  # Use set to avoid duplicate checks
            try:
                logger.info("[FINALIZE] Verifying URL: %s", url)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    verified_urls.append(url)
                    logger.info("[FINALIZE] URL verified: %s", url)
                else:
                    invalid_urls.append(url)
                    logger.warning(
                        "[FINALIZE] URL returned status %d: %s",
                        response.status_code, url
                    )
            except requests.RequestException as e:
                invalid_urls.append(url)
                logger.warning("[FINALIZE] URL verification failed: %s - %s",
                               url, str(e))

        # Remove invalid URLs from the documentation
        for invalid_url in invalid_urls:
            # Remove markdown links with invalid URLs
            service_info_content = re.sub(
                rf'\[([^\]]+)\]\({re.escape(invalid_url)}\)',
                r'\1',
                service_info_content
            )
            # Remove plain invalid URLs
            service_info_content = service_info_content.replace(
                invalid_url, '')

        logger.info(
            "[FINALIZE] Verified %d URLs, removed %d invalid URLs",
            len(verified_urls), len(invalid_urls)
        )

        # Write to file
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(service_info_content)
            logger.info("[FINALIZE] Wrote documentation to %s", filename)
            return {
                "service_info": service_info_content,
                "verified_urls": verified_urls
            }
        except (IOError, OSError) as e:
            logger.error("[FINALIZE] Error writing to file: %s", e)

    result = service_info_content if service_info_content else ""
    return {"service_info": result}


# Create the StateGraph
workflow = StateGraph(GenerationState)

# Add nodes
workflow.add_node("agent", call_agent)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("process", process_tool_results)
workflow.add_node("process_final", finalize_state)

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edges from agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: "process_final",
    }
)

# After tools run, process the results
workflow.add_conditional_edges(
    "tools",
    should_process,
    {
        "process": "process",
        "agent": "agent",
    }
)

# After processing, go back to agent
workflow.add_edge("process", "agent")

# Final processing before end
workflow.add_edge("process_final", END)

# Compile the graph
agent = workflow.compile(debug=DEBUG)
