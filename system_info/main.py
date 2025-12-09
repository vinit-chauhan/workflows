import os

from langchain_core.messages import HumanMessage
from workflow import get_graph, default_state,DEBUG

from phoenix.otel import register

# configure the Phoenix tracer
tracer_provider = register(
    project_name="system-info-workflow",
    auto_instrument=True
)

def write_to_file(result: str, file_name: str):
    """
    Write the result to a file.
    """
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, file_name), "w", encoding="utf-8") as f:
        f.write(result)


def run(product_name: str):
    """
    Run the workflow.
    """
    graph = get_graph()
    state = default_state()
    state["messages"] = [HumanMessage(content=product_name)]

    if DEBUG:
        graph.draw_graph(graph_type="ascii")

    result = graph.run(state)

    if result:
        integration_name = result["integration_name"]
        file_name = f"service_info-{integration_name}.md"
        # Use the verified result if available, otherwise use the unverified result
        content = result.get("final_result", "")
        write_to_file(content, file_name)
        print(f"System info for {product_name} written to file: {file_name}")
    else:
        print("No result")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--product", type=str, required=True)
    args = parser.parse_args()

    run(args.product)
