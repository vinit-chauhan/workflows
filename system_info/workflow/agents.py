from langchain.agents import create_agent

from .constants import pro_llm, DEBUG, flash_llm
from .tools import web_search_tool
from .prompts import (
    PRODUCT_SETUP_EXTERNAL_SYSTEM_PROMPT,
    PRODUCT_SETUP_SYSTEM_PROMPT,
    FINAL_RESULT_GENERATION_SYSTEM_PROMPT,
    SEARCH_RELEVANT_PACKAGE_SYSTEM_PROMPT,
)

product_setup_external_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="product_setup_external_agent",
    system_prompt=PRODUCT_SETUP_EXTERNAL_SYSTEM_PROMPT,
    debug=DEBUG
)


search_relevant_package_agent = create_agent(
    model=flash_llm,
    tools=[web_search_tool],
    debug=DEBUG,
    name="search_relevant_package_agent",
    system_prompt=SEARCH_RELEVANT_PACKAGE_SYSTEM_PROMPT,
)

product_setup_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="product_setup_agent",
    system_prompt=PRODUCT_SETUP_SYSTEM_PROMPT,
    debug=DEBUG
)

final_result_generation_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="final_result_generation_agent",
    system_prompt=FINAL_RESULT_GENERATION_SYSTEM_PROMPT,
    debug=DEBUG
)
