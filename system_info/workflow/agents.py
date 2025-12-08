from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate

from .constants import pro_llm, DEBUG, flash_llm
from .tools import web_search_tool


PRODUCT_SETUP_SYSTEM_PROMPT = """
You are a helpful assistant that finds the product setup instructions for the product.
Setup steps should be a list of detailed steps to configure external logging for the given product.
Use the web_search_tool to find more information about the integration and the setup steps.
A page is more reliable if it is from the official website of the product.
"""

product_setup_agent = create_agent(
    model=pro_llm,
    tools=[web_search_tool],
    name="product_setup_agent",
    system_prompt=PRODUCT_SETUP_SYSTEM_PROMPT,
    debug=DEBUG
)


find_relevant_package_prompt = PromptTemplate(
    template="""Example:
    User input: "Project Discovery Cloud"
    Answer: project_discovery_cloud

    User input: {user_input}
    Answer:""",
    input_variables=["user_input"]
)

FIND_RELEVANT_PACKAGE_SYSTEM_PROMPT = """
You are a helpful assistant that finds the relevant package for the product.
Use the web search tool to find more information about the product and the relevant package.

only return the name of the package, no other text. If name has more than one word, use underscore to join the words.
If you are unable to find the package, return user input in lowercase."""

find_relevant_package_agent = create_agent(
    model=flash_llm,
    tools=[web_search_tool],
    debug=DEBUG,
    name="find_relevant_package_agent",
    system_prompt=FIND_RELEVANT_PACKAGE_SYSTEM_PROMPT,
)
