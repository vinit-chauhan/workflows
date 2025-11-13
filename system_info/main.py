# pylint: disable=C0114,C0116

import os
import sys
import json
import yaml

from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from templates import (
    setup_steps_prompt,
    service_info_prompt,
)

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
)


def get_manifest(integration_name: str) -> dict:
    integration_path = os.environ.get("INTEGRATION_ROOT_PATH")
    if integration_path is None:
        raise ValueError("INTEGRATION_ROOT_PATH is not set")

    with open(
            f"{integration_path}/packages/{integration_name}/manifest.yml",
            "r",
            encoding="utf-8",
    ) as f:
        manifest = yaml.safe_load(f)
        if manifest is None:
            return ""

        return manifest


def generate_service_info(integration_name: str, manifest: dict) -> None:
    # Chain responsible for generating the setup steps
    setup_chain = setup_steps_prompt | llm | StrOutputParser()

    inputs = set()
    for policy_template in manifest["policy_templates"]:
        for inp in policy_template["inputs"]:
            inputs.add(inp["type"])

    # combined chain responsible for generating the service_info.md file
    chain = (
        {
            "integration_name": lambda x: x["integration_name"],
            "collection_via": lambda x: x["collection_via"],
            "setup_steps": setup_chain,
            "manifest": lambda x: x["manifest"]
        }
        | service_info_prompt
        | llm
        | StrOutputParser()
    )

    print("Invoking chains...")
    result = chain.invoke({
        "integration_name": integration_name,
        "collection_via": inputs,
        "manifest": json.dumps(manifest)
    })

    print("Writing service info to file...")
    with open(
            f"service_info-{integration_name}.md", "w",
            encoding="utf-8") as f:
        f.write(result)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: python main.py <integration_name>")
        sys.exit(1)

    manifest = get_manifest(args[0].lower())
    if manifest is None:
        print(f"Manifest for {args[0].lower()} not found")
        sys.exit(1)

    generate_service_info(args[0].lower(), manifest)


if __name__ == "__main__":
    main()
