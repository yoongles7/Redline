# 7-impact: Impact Path Detection

**Task:** Build `analyzer/core/impact.py` — detect flagged impact paths.

**Bobcoins used:** 1.03

**Prompt:** 

Read @SPEC.md and @analyzer/core/reachability.py.

Build analyzer/core/impact.py.

Function: detect_impact_paths(model: dict, graph: dict, reachability: dict) -> list[dict]

For each reachable asset (from reachability), check if the path to it is flagged using the SPEC's flagging rules.

Returns a list of flagged paths. Each path has:{
    "chain": [str, ...],           # ordered node labels from agent to asset
    "length": int,                 # number of edges
    "severity": str,               # CRITICAL / HIGH / MEDIUM / LOW
    "category": str,               # see SPEC category list
    "explanation": str,            # one or two sentences
    "terminal_asset": str,         # asset name
    "operation": str,              # operation on the terminal edge (tool→asset)
}Flagging rules (from SPEC): A path is flagged if ANY of these is true:

    Terminal asset sensitivity >= 4, OR

    The path chains a write/execute operation to a read operation on a different asset, OR

    The path crosses from an internal asset (database, filesystem, credentials) to an external asset (external_api, email, cloud)

Severity mapping (from SPEC):

    sensitivity 5 → CRITICAL

    sensitivity 4 → HIGH

    sensitivity 3 → MEDIUM

    sensitivity 1-2 → LOW

Category mapping:
Determine the category based on the tool's operation and the asset type:

    operation in (write, delete) on database/filesystem → "Data modification" (write) or "Data deletion" (delete)

    operation == execute → "Arbitrary command execution"

    operation == send → "External communication"

    asset type == credentials → "Credential access"

    asset type == cloud → "Privileged infrastructure access"

    asset type == database and operation == read → "Sensitive data access"

    default → "Sensitive data access"

Explanation: Generate a one or two sentence explanation string based on the operation, the tool, and the terminal asset. Example: "execute_sql has EXECUTE access to the customers database. The agent can run arbitrary SQL against customer records."

Note on cross-boundary flagging: For the current MVP, since all paths are length 2 (agent → tool → asset), the cross-boundary rule needs a different interpretation. Implement it as: flag if the terminal asset is external (external_api, email, cloud) AND the agent also reaches an internal asset (database, filesystem, credentials). This detects "this agent can both read internal data and communicate externally," which is the exfiltration concern.

Sorting: Sort flagged paths by severity (CRITICAL > HIGH > MEDIUM > LOW), then by length descending.

Include a test under if __name__ == "__main__": that runs the full pipeline on samples/overprivileged_agent and prints each flagged path.

Do not modify any other files. Only create impact.py.

**Output:** `analyzer/core/impact.py`

**Test result:** overprivileged_agent produces 4 flagged paths:
1. read_customer → customers (HIGH, Sensitive data access)
2. update_customer → customers (HIGH, Data modification)
3. execute_sql → customers (HIGH, Arbitrary command execution)
4. send_email → smtp.example.com (MEDIUM, External communication)