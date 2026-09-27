# 3-inference: Resource and Operation Inference

**Task:** Build `analyzer/core/inference.py` — infers operation and resources per tool via AST body analysis.

**Bobcoins used:** (fill in)

**Prompt:** 

Read @SPEC.md and @analyzer/core/scanner.py.

Build analyzer/core/inference.py.

This module takes the output of scanner.scan_repository() and enriches each tool with operation and resources.

Function: infer_capabilities(scan_result: dict) -> dict

Input: the dict returned by scan_repository.

Output: the same dict, but each tool gets two new fields:{
    "operation": str,           # one of: read, write, delete, execute, send, financial, admin
    "resources": [              # list of dicts
        {
            "name": str,        # e.g. "customer_db", "shell", "/etc/passwd"
            "type": str,        # filesystem | database | external_api | shell | email | cloud | credentials
        },
        ...
    ],
    "inferred": bool            # True if at least one resource was detected, else False
}Behavior:

For each tool, parse its body_source with ast.parse. If parsing fails, set operation to "read" and resources to [] and inferred to False.

Walk the AST body looking for call patterns. Use the detection tables in SPEC.md under "Resource Detection (AST-based)" and "Operation Detection".

For resource detection, match against these patterns:

    open(...), Path(...).read_text(), Path(...).write_text() → filesystem

    psycopg2.connect(...), sqlalchemy.create_engine(...), .execute(...) (on a cursor) → database

    requests.get/post/put/delete(...), httpx.*, urllib.request.* → external_api

    subprocess.run(...), subprocess.Popen(...), os.system(...), os.popen(...) → shell

    smtplib.SMTP(...), smtplib.sendmail(...), sendgrid.* → email

    boto3.client(...), boto3.resource(...) → cloud

    os.environ[...], os.getenv(...), dotenv.load_dotenv(...) → credentials

For the resource name:

    If the call has a string literal argument (e.g. psycopg2.connect("postgresql://localhost/customers")), use a cleaned version of it. For connection strings, extract the database name (customers). For URLs, extract the host. For file paths, use the path as-is.

    If no literal is available, use the resource type as the name (e.g. database, external_api).

For operation detection, match against the SPEC table. If multiple operations match, pick the highest severity using:
admin > financial > execute > delete > write > send > read

Deduplication:

    Within a single tool, deduplicate resources by (name, type).

Include a test under if __name__ == "__main__": that:

    Scans samples/overprivileged_agent

    Runs infer_capabilities

    Prints each tool with its operation and resources in a readable format

Do not modify any other files. Only create inference.py.

**Output:** `analyzer/core/inference.py`

**Test result:** 4 tools enriched:
- read_customer → read / customers (database)
- update_customer → write / customers (database)
- execute_sql → execute / customers (database)
- send_email → send / smtp.example.com (email)