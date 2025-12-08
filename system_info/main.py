from langchain_core.messages import HumanMessage
from workflow import get_graph, default_state


def run(product_name: str):
    graph = get_graph()
    state = default_state()
    state["messages"] = [HumanMessage(content=product_name)]

    graph.draw_graph(graph_type="ascii")

    result = graph.run(state)

    if result:
        print(result)
    else:
        print("No result")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--product", type=str, required=True)
    args = parser.parse_args()

    run(args.product)
