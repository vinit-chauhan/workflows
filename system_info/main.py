from langchain_core.messages import HumanMessage
from workflow import get_graph, default_state


def run():
    graph = get_graph()
    state = default_state()
    state["messages"] = [HumanMessage(content="Darktrack")]

    graph.draw_graph(graph_type="ascii")

    result = graph.run(state)

    if result:
        print(result)
    else:
        print("No result")


if __name__ == "__main__":
    run()
