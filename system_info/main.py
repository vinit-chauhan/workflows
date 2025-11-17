# pylint: disable=C0114,C0116

import sys
from system_info.agent import agent


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: python main.py <integration_name>")
        sys.exit(1)

    integration_name = args[0]
    res = agent.invoke({"integration_name": integration_name})
    print(res.content)
