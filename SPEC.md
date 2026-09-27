# Redline

## What it is

A pre-deployment blast-radius analyzer for LangChain agents.

Given a LangChain Python repository, Redline maps what resources the agent's tools can reach, traces how failures can propagate through those dependencies, and generates safer configuration changes that reduce blast radius without removing required capabilities.

## Core question

> "If this agent goes wrong, how far can the consequences travel?"

## Input

A local filesystem path to a LangChain Python repository.

---

## Discovery

### Agent

* **name** — inferred from the repository directory name, or from the module-level `agent` / `agent_executor` variable name in `agent.py`.
* **purpose** — inferred from the first paragraph of `README.md`, or from the `purpose` field in `config.yaml` if present.

### Tools

Scan every `.py` file in the repository for functions decorated with `@tool`.

For each `@tool` function, extract:

* **name** — the function name
* **description** — the docstring
* **operation** — inferred from the function body (see Operation Detection)
* **resources** — inferred from call patterns in the function body (see Resource Detection)

The MVP supports statically identifiable `@tool` functions. Dynamically generated or unresolved tools are not treated as safely absent; they should be reported as unresolved capabilities.

### Resource Detection (AST-based)

Walk each tool function's AST body looking for the following call patterns:

| Call pattern                                                                      | Resource type | Resource name                                                 |
| --------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------- |
| `open(...)`, `Path(...).read_text()`, `Path(...).write_text()`                    | filesystem    | path literal if present, otherwise `unknown_path`             |
| `psycopg2.connect(...)`, `sqlalchemy.create_engine(...)`, cursor `.execute(...)`  | database      | connection string if present, otherwise `database`            |
| `requests.get/post/put/delete(...)`, `httpx.*`, `urllib.request.*`                | external_api  | URL host if present, otherwise `external_api`                 |
| `subprocess.run(...)`, `subprocess.Popen(...)`, `os.system(...)`, `os.popen(...)` | shell         | `shell`                                                       |
| `smtplib.SMTP(...)`, `smtplib.sendmail(...)`, `sendgrid.*`                        | email         | `email`                                                       |
| `boto3.client(...)`, `boto3.resource(...)`, `google.cloud.*`, `azure.*`           | cloud         | service name if present, otherwise `cloud`                    |
| `os.environ[...]`, `os.getenv(...)`, `dotenv.load_dotenv(...)`                    | credentials   | environment variable name if present, otherwise `credentials` |

If no known call patterns are found, mark the tool with:

```json
{
  "resources": [],
  "inferred": false
}
```

Resource detection is static and may over-approximate actual runtime behavior.

### Operation Detection

Infer the operation from the call patterns found in the tool body:

| Call pattern                                                                     | Operation |
| -------------------------------------------------------------------------------- | --------- |
| `.read()`, `.read_text()`, `requests.get`, `os.getenv`, `SELECT`                 | read      |
| `.write()`, `.write_text()`, `requests.post`, `requests.put`, `INSERT`, `UPDATE` | write     |
| `requests.delete`, `DELETE`, `os.remove`, `os.unlink`, `.unlink()`               | delete    |
| `subprocess.run`, `os.system`, `os.popen`, `exec(`, `eval(`                      | execute   |
| `smtplib.sendmail`, `sendgrid.send`, `.send()`                                   | send      |
| `stripe.*`, `paypal.*`, `payment`, `charge`                                      | financial |
| `boto3.client('iam')`, `chmod`, `chown`, `.grant()`                              | admin     |

If multiple operation patterns match, assign the highest-impact operation using:

```text
admin > financial > execute > delete > write > send > read
```

This is a conservative static-analysis heuristic and may over-approximate the actual behavior of a tool.

### Asset Deduplication Rule

Assets are **global to the agent**.

If three tools all access `customer_db`, that is **one asset** with three incoming capability edges.

The asset name is the detected resource name, for example:

```text
customer_db
```

Each asset has:

* **name**
* **type** — one of `database`, `filesystem`, `external_api`, `email`, `shell`, `credentials`, `cloud`
* **sensitivity** — integer from 1–5
* **reached_by** — list of tool names

The operation belongs to the tool-to-asset capability edge, not to the asset itself.

For example:

```text
Agent
  ↓
execute_sql
  ↓ EXECUTE
customer_db
```

The same `customer_db` asset may therefore be reached by multiple tools with different operations.

### Sensitivity Values and Rationale

| Resource type | Sensitivity | Why                                                                            |
| ------------- | ----------: | ------------------------------------------------------------------------------ |
| filesystem    |           2 | Local file access; scope is bounded but may include secrets                    |
| external_api  |           3 | Reaches outside the trust boundary; data may leave the organization            |
| email         |           3 | External communication channel; data may leave the organization                |
| database      |           4 | Structured data may contain PII or business records                            |
| shell         |           5 | Arbitrary command execution may reach other resources available to the process |
| credentials   |           5 | Secrets may unlock access to other systems                                     |
| cloud         |           5 | Cloud infrastructure may affect live systems                                   |

These are default sensitivity values used by the MVP. They are heuristic classifications, not guarantees about the actual contents or privileges of a resource.

### Controls

Detect known control patterns in the repository:

* **human_approval**

  * `interrupt`
  * explicit `approve` / `confirm` patterns around high-impact operations
  * known approval wrappers
  * generic `input()` alone is not sufficient evidence of human approval

* **rate_limits**

  * `rate_limit`
  * `max_calls`
  * `throttle`

* **rollback / recovery**

  * explicit `rollback`
  * `undo`
  * `revert`
  * recovery logic associated with a high-impact operation

* **sandbox**

  * `sandbox`
  * `restricted`
  * `allowlist`

For each control type, calculate coverage as:

```text
coverage =
(number of high-impact tools gated by this control)
/
(total number of high-impact tools)
```

High-impact tools are tools whose operation is one of:

```text
execute, delete, financial, admin
```

If there are no high-impact tools, coverage is defined as `1.0`.

Control detection is static and may not prove that a control completely prevents an operation.

---

## Processing

### 1. Capability Graph

Build a directed graph:

```text
Agent → Tool → Asset
```

Every edge represents a capability or dependency.

* The agent is a single node.
* Each tool is a unique node.
* Each asset is a unique global node.
* Tool-to-asset edges contain the detected operation.

Example:

```text
Agent
  ↓
update_customer
  ↓ WRITE
customer_db
```

If a tool accesses multiple assets, it has an edge to each asset.

### 2. Reachability

Perform BFS from the agent node.

Return:

* all reachable asset nodes
* the shortest path length from the agent to each asset

Path length is the number of graph edges traversed.

For example:

```text
Agent → Tool
```

has length `1`.

```text
Agent → Tool → Asset
```

has length `2`.

### 3. Impact Paths

An impact path is any traversal from the agent to an asset with length **at least 2 edges**.

Examples:

```text
Agent → Tool → Asset
```

or:

```text
Agent → Tool → Asset → Asset
```

if additional dependency edges are represented.

The minimum valid impact path is therefore:

```text
Agent → Tool → Asset
```

Path length describes propagation depth and is **not itself a severity indicator**.

A path is **flagged** if any of the following is true:

* the terminal asset has sensitivity `>= 4`, OR
* the path chains a write/execute operation to a read operation on a different asset, OR
* the path crosses from an internal asset (`database`, `filesystem`, `credentials`) to an external asset (`external_api`, `email`, `cloud`)

Flagged paths are sorted by:

1. severity, descending
2. path length, descending

Each flagged path contains:

* **chain** — ordered list of node labels, e.g. `["agent", "execute_sql", "customer_db"]`
* **length** — number of edges
* **severity** — based on the highest-sensitivity asset reached:

  * sensitivity `5` → `CRITICAL`
  * sensitivity `4` → `HIGH`
  * sensitivity `3` → `MEDIUM`
  * sensitivity `1–2` → `LOW`
* **category** — one of:

  * Sensitive data access
  * Data modification
  * Data deletion
  * External communication
  * Arbitrary command execution
  * Credential access
  * Privileged infrastructure access
* **explanation** — one or two sentences explaining why the path was flagged

Static analysis should describe what the graph establishes rather than claiming that an actual compromise will occur.

### 4. Blast Radius Metrics

Calculate:

* **reachable_assets** — count of all reachable asset nodes
* **sensitive_assets** — count of reachable assets with sensitivity `>= 4`
* **write_capable_assets** — count of reachable assets touched by a tool whose operation is `write`, `delete`, `execute`, `financial`, or `admin`
* **max_depth** — longest path length from the agent to any asset
* **high_impact_tools** — count of tools whose operation is `execute`, `delete`, `financial`, or `admin`
* **approval_coverage** — control coverage from the Controls section
* **recovery_coverage** — control coverage from the Controls section

`max_depth` is reported as a propagation metric. It is not treated as a direct measure of severity.

### 5. Blast Radius Score (0–100)

The blast-radius score is a transparent heuristic summarizing several measurable properties of the agent's reachable capabilities.

Normalization:

```text
normalized_sensitive_assets = min(sensitive_assets / 5, 1.0)

normalized_write_capable = min(write_capable_assets / 5, 1.0)
```

Score:

```text
score = (
    0.35 * normalized_sensitive_assets +
    0.25 * normalized_write_capable +
    0.15 * (1 - approval_coverage) +
    0.10 * (1 - recovery_coverage) +
    0.15 * normalized_high_impact_tools
) * 100
```

where:

```text
normalized_high_impact_tools = min(high_impact_tools / 5, 1.0)
```

The score does **not** include `max_depth`, because path depth describes propagation structure rather than impact by itself.

Score bands:

```text
0–25   → LOW
26–50  → MEDIUM
51–75  → HIGH
76–100 → CRITICAL
```

The score is not a probability of failure, probability of compromise, or prediction of actual harm. The individual metrics and flagged impact paths must always be shown alongside the score.

### Worked Example

Given `overprivileged_agent`:

* reachable_assets = `3` (`customer_db`, `email`, `external_api`)
* sensitive_assets = `1` (`customer_db`, sensitivity 4)
* write_capable_assets = `1` (`customer_db`)
* max_depth = `2` (`agent → execute_sql → customer_db`)
* high_impact_tools = `1` (`execute_sql`)
* approval_coverage = `0.0`
* recovery_coverage = `0.0`

Normalization:

```text
normalized_sensitive_assets = min(1 / 5, 1) = 0.20

normalized_write_capable = min(1 / 5, 1) = 0.20

normalized_high_impact_tools = min(1 / 5, 1) = 0.20
```

Score:

```text
score =
    (0.35 * 0.20)
  + (0.25 * 0.20)
  + (0.15 * 1.0)
  + (0.10 * 1.0)
  + (0.15 * 0.20)

= 0.07 + 0.05 + 0.15 + 0.10 + 0.03

= 0.40
```

```text
→ 40 / 100

Band: MEDIUM
```

### 6. Mitigation Candidates

Select mitigation candidates from the highest-severity flagged impact path.

1. Find the highest-severity flagged impact path.
2. Identify the tool node responsible for the path.
3. Generate applicable mitigation candidates for that tool, such as:

   * remove the tool
   * restrict the tool's resource scope
   * change the operation to read-only where applicable
   * require human approval
   * add a sandbox or allowlist
   * add rate limiting
4. Apply each candidate to a copy of the security model.
5. Re-run all metrics and the blast-radius score.
6. Produce a before/after comparison for each candidate.

If multiple paths share the highest severity:

1. select the longest path
2. if still tied, select the alphabetically first path

The mitigation process must not automatically modify the source repository.

Each candidate should report:

* proposed action
* affected tool
* reason
* expected impact
* before metrics
* after metrics

The purpose of mitigation is to reduce blast radius while preserving required capabilities.

---

## Output

Structured report:

```text
agent_name
intended_purpose

blast_radius:
  score
  band
  metrics

impact_paths:
  - chain
    length
    severity
    category
    explanation

findings:
  - title
    severity
    description

mitigation:
  candidates:
    - action
      tool
      reason
      expected_impact
      before
      after
```

Only `CRITICAL` and `HIGH` impact paths generate findings.

The report should make the reasoning behind the score and recommendations visible rather than presenting the score as a standalone security judgment.

---

## Scope Disclaimer

Redline covers static pre-deployment analysis of LangChain agents.

It does **not** cover:

* runtime behavior
* prompt injection
* memory poisoning
* multi-agent dynamics

Redline's findings describe capabilities and potential propagation paths inferred from the repository. They do not establish that a vulnerability will be exploitable at runtime.

---

## Sample Data

Samples are synthetic repositories in `samples/`.

Public repositories used for validation are listed in `README.md`.