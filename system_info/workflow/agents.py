from langchain.agents import create_agent

from .constants import pro_llm, DEBUG, flash_llm
from .tools import fetch_url_content, web_search_tool
from .prompts import (
    SETUP_INSTRUCTIONS_EXTERNAL_INFO_SYSTEM_PROMPT,
    SETUP_INSTRUCTIONS_CONTEXT_SYSTEM_PROMPT,
    FINAL_RESULT_GENERATION_SYSTEM_PROMPT,
    SEARCH_RELEVANT_PACKAGE_SYSTEM_PROMPT,
    URL_VERIFIER_SYSTEM_PROMPT,
)

setup_instructions_external_info_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="setup_instructions_external_info_agent",
    system_prompt=SETUP_INSTRUCTIONS_EXTERNAL_INFO_SYSTEM_PROMPT,
    debug=DEBUG
)


search_relevant_package_agent = create_agent(
    model=flash_llm,
    tools=[web_search_tool],
    debug=DEBUG,
    name="search_relevant_package_agent",
    system_prompt=SEARCH_RELEVANT_PACKAGE_SYSTEM_PROMPT,
)

setup_instructions_context_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="setup_instructions_context_agent",
    system_prompt=SETUP_INSTRUCTIONS_CONTEXT_SYSTEM_PROMPT,
    debug=DEBUG
)

final_result_generation_agent = create_agent(
    model=flash_llm,
    tools=[web_search_tool],
    name="final_result_generation_agent",
    system_prompt=FINAL_RESULT_GENERATION_SYSTEM_PROMPT,
    debug=DEBUG
)

url_verifier_agent = create_agent(
    model=flash_llm,
    tools=[fetch_url_content],
    name="url_verifier_agent",
    system_prompt=URL_VERIFIER_SYSTEM_PROMPT,
    debug=DEBUG
)
