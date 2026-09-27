
---

**Status:** active  **Date:** 2026-09-27

---

### 👤 User

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

---

### 🤖 Assistant

> 🔧 called: read_file, read_file

Let me read the SPEC.md and graph.py files first.

> 🔧 **read_file** — SPEC.md

> 🔧 **read_file** — analyzer/core/graph.py

### 🤖 Assistant

> 🔧 called: list_files

Now let me check what other core modules exist to understand the pipeline:

> 🔧 **list_files** — analyzer/core

### 🤖 Assistant

> 🔧 called: write_file

Good. Now I have everything I need. Let me write [`analyzer/core/reachability.py`](analyzer/core/reachability.py):

> 🔧 **write_file** — analyzer/core/reachability.py

### 🤖 Assistant

> 🔧 called: execute_command

Now run the smoke test:

> 🔧 **execute_command** — python analyzer/core/reachability.py

### 🤖 Assistant

> 🔧 called: execute_command

Works. The SPEC's worked example lists 3 reachable assets (`customer_db`, `email`, `external_api`) — let me quickly check what the scanner actually finds in `overprivileged_agent` to make sure this is the expected count from the current sample data:

> 🔧 **execute_command** — python -c "
import sys; sys.path.insert(0, '.')
from analyzer.core import scanner, inference
from analyzer.core.model import build_model
sample = 'samples/overprivileged_agent'
scan = scanner.scan_repository(sample)
enriched = inference.infer_capabilities(scan)
model = build_model(enriched, sample)
print('tools:', [t['name'] for t in model['tools']])
print('assets:', [(a['name'], a['type'], a['sensitivity']) for a in model['assets']])
"


### 🤖 Assistant

> 🔧 called: execute_command

The sample data has 2 assets in the model. The BFS finds both of them correctly. The SPEC's worked example uses different tool/asset names than what's in the actual sample files — the implementation is correct, the gap is in the sample data, not in `reachability.py`.

Let me also verify the BFS correctly picks up assets reached via multiple tools (e.g. `customers` is reached by both `read_customer`, `update_customer`, and `execute_sql`) and records only the first visit:

> 🔧 **execute_command** — python -c "
import sys; sys.path.insert(0, '.')
from analyzer.core import scanner, inference
from analyzer.core.model import build_model
from analyzer.core.graph import build_graph
from analyzer.core.reachability import compute_reachability

sample = 'samples/overprivileged_agent'
scan = scanner.scan_repository(sample)
enriched = inference.infer_capabilities(scan)
model = build_model(enriched, sample)
graph = build_graph(model)

print('Graph edges:')
for e in graph['edges']:
    print(' ', e)

print()
result = compute_reachability(graph)
for a in result['reachable_assets']:
    print(a)
"


### 🤖 Assistant

`asset:customers` is reachable via three tools (`read_customer`, `update_customer`, `execute_sql`) all at depth 2 — BFS correctly records only the first encounter (shortest path, first encountered per the spec), capturing `read_customer` as the path. Both assets are found, depths are correct.

---

[`analyzer/core/reachability.py`](analyzer/core/reachability.py) is complete. Here's what was built:

**Algorithm**

1. **Adjacency map** — built from `graph["edges"]` as `{from_id: [(to_id, op, sensitivity)]}`.
2. **Asset metadata map** — scans edges to collect max sensitivity per `asset:*` node (since `graph.py` stores sensitivity on edges, not on nodes).
3. **BFS from `"agent"`** — standard visited-set BFS. Tool nodes are enqueued for further traversal; asset nodes are recorded and *not* enqueued (they are leaf nodes in this graph structure), so the first visit is always the shortest path.
4. **Result assembly** — assets sorted by depth; `max_depth` and `total_reachable` derived from the list.

**Output matches the spec** — each asset entry carries `id`, `label`, `type` (empty string unless the node gains a `type` key in a future graph version), `sensitivity`, `depth`, `path` (node ids), and `path_labels` (human-readable labels).

**`type` field note** — `graph.py` doesn't embed asset type on graph nodes (it only stores `id`, `label`, `kind`). The field is included in the return shape per the spec and is left as `""` unless the graph node itself carries a `"type"` key. Callers needing the type should augment from the model's `assets` list.