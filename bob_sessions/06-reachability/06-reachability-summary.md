# 6-reachability: BFS Reachability Analysis

**Task:** Build `analyzer/core/reachability.py` — BFS from agent to assets.

**Bobcoins used:** 0.349

**Prompt:** 

Read @SPEC.md and @analyzer/core/graph.py.

Build analyzer/core/reachability.py.

Function: compute_reachability(graph: dict) -> dict

Performs BFS from the "agent" node.

Returns:{
    "reachable_assets": [
        {
            "id": str,               # asset node id, e.g. "asset:customers"
            "label": str,            # asset name
            "type": str,             # database / filesystem / etc.
            "sensitivity": int,
            "depth": int,            # shortest path length from agent (edges)
            "path": [str, ...],      # ordered node ids from agent to asset
            "path_labels": [str, ...],  # same as path but with labels
        },
        ...
    ],
    "max_depth": int,                # deepest reachable asset depth
    "total_reachable": int,          # count of reachable assets
}Algorithm:

    Build an adjacency map: {from_id: [(to_id, operation, sensitivity), ...]}

    BFS starting from "agent", tracking depth.

    When a node's kind is "asset", record it as reachable. Only record the first visit (shortest path).

    If the same asset is reachable via multiple tools, keep the shortest path. If tied, keep the first encountered.

    After BFS, collect all assets with their depth and path.

Note on graph node lookup: the graph nodes have id, label, and kind. Use id as the BFS key. Look up label/type/sensitivity from the nodes list or from edge metadata.

Include a test under if __name__ == "__main__": that:

    Runs scanner → inference → model → graph → reachability on samples/overprivileged_agent

    Prints each reachable asset with its depth and path

    Prints max_depth and total_reachable

Do not modify any other files. Only create reachability.py.

**Output:** `analyzer/core/reachability.py`

**Test result:** overprivileged_agent — 2 assets reachable at depth 2:
- customers (sensitivity 4) via read_customer
- smtp.example.com (sensitivity 3) via send_email