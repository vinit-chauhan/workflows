from typing import Literal

from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .state import WorkflowState
from .nodes import (
    find_relevant_packages_node,
    get_package_info_node,
    find_relevant_package_node,
    setup_instructions_node,

    is_existing_integration,
)


class WorkflowGraph:
    """
    A graph for the workflow.
    """
    compiled_graph: CompiledStateGraph = None

    def __init__(self) -> None:
        if not self.compiled_graph:
            self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        graph: StateGraph[WorkflowState] = StateGraph(WorkflowState)

        # Adding nodes to the graph
        graph.add_node("find_relevant_packages", find_relevant_packages_node)
        graph.add_node("get_package_info", get_package_info_node)
        graph.add_node("setup_instructions",
                       setup_instructions_node)
        graph.add_node("find_relevant_package", find_relevant_package_node)

        # Adding edges between nodes
        graph.add_edge(START, "find_relevant_packages")
        graph.add_conditional_edges("find_relevant_packages", is_existing_integration, {
            "yes": "get_package_info",
            "no": "find_relevant_package"
        })
        graph.add_edge("find_relevant_package", "setup_instructions")
        graph.add_edge("get_package_info", "setup_instructions")
        graph.add_edge("setup_instructions", END)

        self.compiled_graph = graph.compile()

    def draw_graph(self, graph_type: Literal["ascii", "mermaid"] = "ascii") -> None:
        """
        Draws the graph.
        """
        match graph_type:
            case "ascii":
                print(self.compiled_graph.get_graph().draw_ascii())
            case "mermaid":
                print(self.compiled_graph.get_graph().draw_mermaid())

    def run(self, state: WorkflowState) -> WorkflowState:
        """
        Runs the workflow.
        """
        return self.compiled_graph.invoke(state)


def get_graph() -> WorkflowGraph:
    """
    Returns the graph for the workflow.
    """
    return WorkflowGraph()
