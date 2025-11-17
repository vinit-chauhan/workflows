# pylint: disable=C0114,C0116,C0301
# flake8: noqa: E501

import sys

from langchain_core.messages import HumanMessage

from agent import agent
from agent.state import GenerationState


def agent_main(integration_name: str):
    print(f"\n{'='*60}")
    print(f"🚀 Starting agent for integration: {integration_name}")
    print(f"{'='*60}\n")

    initial_state: GenerationState = {
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
    }

    result = agent.invoke(initial_state)

    if "messages" in result and len(result["messages"]) > 0:
        # system_info = result["messages"][-1].content

        # documentation = ""

        # if isinstance(system_info, list):
        #     # Handle list of content blocks (common with some LLMs)
        #     for item in system_info:
        #         if isinstance(item, dict) and 'text' in item:
        #             documentation += item['text']
        #         elif hasattr(item, 'text'):
        #             documentation += item.text
        #         else:
        #             documentation += item
        # else:
        #     documentation += system_info

        # with open("service_info.md", "w", encoding="utf-8") as f:
        #     f.write(documentation)

        print("✅ Generation complete!")
        sys.exit(0)
    else:
        print("\n❌ [ERROR] No service info generated")
        sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: python main.py <integration_name>")
        sys.exit(1)

    agent_main(args[0])
