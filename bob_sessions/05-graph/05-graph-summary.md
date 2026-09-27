# 5-graph: Capability Graph

**Task:** Build `analyzer/core/graph.py` — directed graph of Agent → Tool → Asset.

**Bobcoins used:** 0.249

**Prompt:** 

Read @SPEC.md and @analyzer/core/model.py.

Build analyzer/core/graph.py.

This module takes the Agent Security Model and produces a directed capability graph.

Function: build_graph(model: dict) -> dict

Returns a simple adjacency representation:{
    "nodes": [
        {"id": str, "label": str, "kind": str},   # kind: "agent" | "tool" | "asset"
        ...
    ],
    "edges": [
        {
            "from": str,     # source node id
            "to": str,       # target node id
            "operation": str,   # read/write/delete/execute/send/financial/admin  (None for agent→tool)
            "sensitivity": int, # for tool→asset edges only; None otherwise
        },
        ...
    ],
}Node IDs:

    Agent node: "agent" (always)

    Tool nodes: "tool:" + tool_name (e.g., "tool:read_customer")

    Asset nodes: "asset:" + asset_name (e.g., "asset:customers")

Edges:

    Agent → each tool: one edge per tool. operation=None, sensitivity=None.

    Tool → each asset it reaches: one edge per (tool, asset). operation = tool's operation. sensitivity = asset's sensitivity.

Note: Use the model's tools[*].resources list (asset names) and the model's assets list to look up sensitivity.

Function: graph_to_dot(graph: dict) -> str

Returns a Graphviz DOT string representation of the graph for visualization. Nodes colored by kind:

    agent → blue

    tool → orange

    asset → red if sensitivity >= 4, else grey

Include a test under if __name__ == "__main__": that:

    Runs scanner → inference → model → build_graph on samples/overprivileged_agent

    Prints the node count, edge count, and the full DOT string

Do not modify any other files. Only create graph.py.

**Output:** `analyzer/core/graph.py`

**Test result:** overprivileged_agent produces 7 nodes, 8 edges. DOT output valid with color-coded nodes (agent=blue, tool=orange, sensitive asset=red).