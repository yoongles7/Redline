
---

**Status:** active  **Date:** 2026-09-27

---

### 👤 User

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

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me start by reading the spec and model files to understand the domain.

> 🔧 **read_file** — SPEC.md

> 🔧 **read_file** — analyzer/core/model.py

### 🤖 Assistant

> 🔧 called: list_files, list_files

Now let me look at the existing core modules to understand how scanner and inference work, plus the sample:

> 🔧 **list_files** — analyzer/core

> 🔧 **list_files** — samples/overprivileged_agent

### 🤖 Assistant

> 🔧 called: write_file

Now I have everything I need. The model structure is clear:

- `model["agent"]` → `{name, purpose}`
- `model["tools"]` → list of `{name, operation, resources: [asset_name, ...]}`
- `model["assets"]` → list of `{name, type, sensitivity, reached_by}`

The `resources` list in tools contains asset names (strings), and the `assets` list is deduplicated globally. I can build a sensitivity lookup from `assets`.

> 🔧 **write_file** — analyzer/core/graph.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let's run the smoke test to validate it:

> 🔧 **execute_command** — cd /home/yoongles/redline && python analyzer/core/graph.py

### 🤖 Assistant

The smoke test runs cleanly. Let me verify the output is correct against the SPEC's worked example:

- **7 nodes**: `agent` + 4 tools (`read_customer`, `update_customer`, `execute_sql`, `send_email`) + 2 assets (`customers`, `smtp.example.com`) ✓
- **8 edges**: 4 agent→tool + 4 tool→asset ✓  
- `customers` is **red** (database → sensitivity 4 ≥ 4) ✓  
- `smtp.example.com` is **grey** (email → sensitivity 3 < 4) ✓  
- Asset deduplication works: `customers` appears as a single node reached by 3 tools, with each tool having its own edge carrying its own operation (`READ`, `WRITE`, `EXECUTE`) ✓

Here's a summary of what was built:

---

**[`analyzer/core/graph.py`](analyzer/core/graph.py)**

### `build_graph(model)`
Walks the model's `tools` list and emits three classes of nodes/edges:

| What | ID format | Kind |
|---|---|---|
| Single agent node | `"agent"` | `"agent"` |
| One node per tool | `"tool:<name>"` | `"tool"` |
| One node per asset (deduplicated) | `"asset:<name>"` | `"asset"` |

Agent→tool edges carry `operation=None, sensitivity=None`. Tool→asset edges carry the tool's `operation` and the asset's `sensitivity` looked up from `model["assets"]`.

### `graph_to_dot(graph)`
Produces a left-to-right DOT digraph. Node colours follow the spec:
- **Agent** → `deepskyblue` ellipse  
- **Tool** → `orange` box  
- **Asset** → `red` cylinder if sensitivity ≥ 4, `lightgrey` otherwise  

Edge labels show the operation in uppercase (agent→tool edges are unlabelled).

### `_dot_id(node_id)`
Converts IDs like `"tool:read_customer"` to valid DOT identifier tokens by replacing `:`, `-`, and spaces with `_`.