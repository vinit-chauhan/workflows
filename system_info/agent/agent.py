# pylint: disable=C0114,C0116
from typing import List
from langchain.agents import create_agent
from langchain.tools import BaseTool

from .constants import MODEL
from .tools import (
    read_manifest,
    write_service_info,
    verify_url,
)
from .prompts import SYSTEM_PROMPT
from .state import GenerationState


tools: List[BaseTool] = [
    read_manifest,
    write_service_info,
    verify_url,
]

agent = create_agent(
    model=MODEL,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    debug=True,
    state_schema=GenerationState,
)
