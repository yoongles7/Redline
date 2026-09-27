"""
inference.py — enriches scanner output with operation and resource inference.

Takes the dict returned by scanner.scan_repository() and adds three fields to
each tool entry:

    operation  : str   — highest-severity operation detected
    resources  : list  — [{name, type}, ...] deduplicated
    inferred   : bool  — True if at least one resource was detected
"""

import ast
import re
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Operation priority (higher index = higher severity)
# ---------------------------------------------------------------------------

_OPERATION_RANK = {
    "read": 0,
    "send": 1,
    "write": 2,
    "delete": 3,
    "execute": 4,
    "financial": 5,
    "admin": 6,
}


def _higher_op(a, b):
    """Return whichever operation has the higher severity rank."""
    return a if _OPERATION_RANK.get(a, 0) >= _OPERATION_RANK.get(b, 0) else b


# ---------------------------------------------------------------------------
# Helpers for extracting a "name" from call arguments
# ---------------------------------------------------------------------------

def _first_string_arg(call_node):
    """Return the first positional string-literal argument of a Call node, or None."""
    if not call_node.args:
        return None
    first = call_node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _extract_db_name(value):
    """
    Pull a database/service name out of a connection string or URL.

    postgresql://localhost/customers  →  customers
    sqlite:///app.db                  →  app.db
    fallback                          →  the raw value
    """
    try:
        parsed = urlparse(value)
        # path is like /customers or /app.db
        if parsed.path and parsed.path != "/":
            return parsed.path.lstrip("/").split("/")[0]
    except Exception:
        pass
    return value


def _extract_url_host(value):
    """Extract the hostname from a URL string, falling back to the raw value."""
    try:
        parsed = urlparse(value)
        if parsed.hostname:
            return parsed.hostname
    except Exception:
        pass
    return value


# ---------------------------------------------------------------------------
# AST visitor
# ---------------------------------------------------------------------------

class _CapabilityVisitor(ast.NodeVisitor):
    """
    Walks an AST and accumulates detected operations and resources.

    Public attributes after visiting:
        operations : list[str]
        resources  : list[dict]  — {name, type}; deduplicated by (name, type)
    """

    def __init__(self):
        self.operations = []
        self._resources_seen = set()   # (name, type) tuples for dedup
        self.resources = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_op(self, op):
        self.operations.append(op)

    def _add_resource(self, name, rtype):
        key = (name, rtype)
        if key not in self._resources_seen:
            self._resources_seen.add(key)
            self.resources.append({"name": name, "type": rtype})

    # ------------------------------------------------------------------
    # Attribute-access helpers: decompose a.b.c into ["a", "b", "c"]
    # ------------------------------------------------------------------

    @staticmethod
    def _attr_chain(node):
        """Return the dotted name chain for an Attribute or Name node."""
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        parts.reverse()
        return parts

    @staticmethod
    def _path_call_arg(func_node):
        """
        Given the func node of a chained call like Path(path).read_text(),
        return the first string argument of the outer Path(...) call, or None.

        AST shape:
            Attribute(value=Call(func=Name('Path'), args=[...]), attr='read_text')
        """
        if not isinstance(func_node, ast.Attribute):
            return None
        inner = func_node.value
        if not isinstance(inner, ast.Call):
            return None
        inner_func = inner.func
        is_path = (
            (isinstance(inner_func, ast.Name) and inner_func.id == "Path")
            or (
                isinstance(inner_func, ast.Attribute)
                and inner_func.attr == "Path"
            )
        )
        if not is_path:
            return None
        return _first_string_arg(inner)

    # ------------------------------------------------------------------
    # Visitor entry-point for Call nodes
    # ------------------------------------------------------------------

    def visit_Call(self, node):  # noqa: N802
        self._handle_call(node)
        self.generic_visit(node)

    def _handle_call(self, node):
        func = node.func

        # --- open(...) ---------------------------------------------------
        if isinstance(func, ast.Name) and func.id == "open":
            arg = _first_string_arg(node)
            name = arg if arg else "unknown_path"
            self._add_resource(name, "filesystem")
            # open() for writing or appending → write op; otherwise read
            mode_arg = None
            if len(node.args) >= 2:
                a = node.args[1]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    mode_arg = a.value
            if mode_arg and any(c in mode_arg for c in ("w", "a", "x")):
                self._add_op("write")
            else:
                self._add_op("read")
            return

        # --- exec(...) / eval(...) ----------------------------------------
        if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
            self._add_op("execute")
            return

        chain = self._attr_chain(func)
        if not chain:
            return

        dotted = ".".join(chain)
        root = chain[0]
        leaf = chain[-1]

        # --- Path(...).read_text() / Path(...).write_text() ---------------
        # AST: Attribute(value=Call(func=Name('Path'), args=[...]), attr='read_text')
        # _attr_chain() stops at the inner Call node, so chain == ['read_text'].
        if leaf == "read_text":
            path_arg = self._path_call_arg(func)
            name = path_arg if path_arg else "unknown_path"
            self._add_resource(name, "filesystem")
            self._add_op("read")
            return

        if leaf == "write_text":
            path_arg = self._path_call_arg(func)
            name = path_arg if path_arg else "unknown_path"
            self._add_resource(name, "filesystem")
            self._add_op("write")
            return

        # --- psycopg2.connect(...) ----------------------------------------
        if dotted == "psycopg2.connect":
            arg = _first_string_arg(node)
            name = _extract_db_name(arg) if arg else "database"
            self._add_resource(name, "database")
            # connecting itself is neutral; operation determined by execute()
            return

        # --- sqlalchemy.create_engine(...) --------------------------------
        if dotted == "sqlalchemy.create_engine":
            arg = _first_string_arg(node)
            name = _extract_db_name(arg) if arg else "database"
            self._add_resource(name, "database")
            return

        # --- cursor .execute(...) -----------------------------------------
        # Matches any variable name whose last attribute call is .execute(...)
        # but NOT subprocess.* (handled separately)
        if leaf == "execute" and root not in ("subprocess",):
            self._add_resource("database", "database")
            # Inspect the SQL string to determine operation
            arg = _first_string_arg(node)
            if arg:
                upper = arg.strip().upper()
                if upper.startswith("SELECT"):
                    self._add_op("read")
                elif upper.startswith(("INSERT", "UPDATE")):
                    self._add_op("write")
                elif upper.startswith("DELETE"):
                    self._add_op("delete")
                else:
                    self._add_op("execute")
            else:
                # Unknown SQL → conservative: execute
                self._add_op("execute")
            return

        # --- requests.* ---------------------------------------------------
        if root == "requests" and leaf in ("get", "post", "put", "delete",
                                           "patch", "request", "head"):
            arg = _first_string_arg(node)
            name = _extract_url_host(arg) if arg else "external_api"
            self._add_resource(name, "external_api")
            op_map = {
                "get": "read", "head": "read",
                "post": "write", "put": "write", "patch": "write",
                "delete": "delete",
            }
            self._add_op(op_map.get(leaf, "write"))
            return

        # --- httpx.* ------------------------------------------------------
        if root == "httpx":
            arg = _first_string_arg(node)
            name = _extract_url_host(arg) if arg else "external_api"
            self._add_resource(name, "external_api")
            op_map = {
                "get": "read", "head": "read",
                "post": "write", "put": "write", "patch": "write",
                "delete": "delete",
            }
            self._add_op(op_map.get(leaf, "write"))
            return

        # --- urllib.request.* ---------------------------------------------
        if chain[:2] == ["urllib", "request"]:
            arg = _first_string_arg(node)
            name = _extract_url_host(arg) if arg else "external_api"
            self._add_resource(name, "external_api")
            self._add_op("read")
            return

        # --- subprocess.run / subprocess.Popen ---------------------------
        if dotted in ("subprocess.run", "subprocess.Popen"):
            self._add_resource("shell", "shell")
            self._add_op("execute")
            return

        # --- os.system / os.popen ----------------------------------------
        if dotted in ("os.system", "os.popen"):
            self._add_resource("shell", "shell")
            self._add_op("execute")
            return

        # --- os.remove / os.unlink ----------------------------------------
        if dotted in ("os.remove", "os.unlink"):
            arg = _first_string_arg(node)
            name = arg if arg else "unknown_path"
            self._add_resource(name, "filesystem")
            self._add_op("delete")
            return

        # --- .unlink() (pathlib) ------------------------------------------
        if leaf == "unlink":
            self._add_resource("unknown_path", "filesystem")
            self._add_op("delete")
            return

        # --- smtplib.SMTP(...) / smtplib.sendmail(...)  ------------------
        if dotted == "smtplib.SMTP":
            arg = _first_string_arg(node)
            name = arg if arg else "email"
            self._add_resource(name, "email")
            return

        if leaf == "sendmail" and root == "smtplib":
            self._add_resource("email", "email")
            self._add_op("send")
            return

        # .sendmail() on any object
        if leaf == "sendmail":
            self._add_resource("email", "email")
            self._add_op("send")
            return

        # --- sendgrid.* ---------------------------------------------------
        if root == "sendgrid":
            self._add_resource("email", "email")
            if leaf in ("send", "sendmail"):
                self._add_op("send")
            return

        # --- .send() (generic "send" method) ------------------------------
        if leaf == "send":
            self._add_op("send")
            return

        # --- boto3.client(...) / boto3.resource(...) ----------------------
        if root == "boto3" and leaf in ("client", "resource"):
            arg = _first_string_arg(node)
            name = arg if arg else "cloud"
            self._add_resource(name, "cloud")
            # boto3.client('iam') → admin
            if arg and arg.strip().lower() == "iam":
                self._add_op("admin")
            return

        # --- google.cloud.* -----------------------------------------------
        if chain[:2] == ["google", "cloud"]:
            self._add_resource("cloud", "cloud")
            return

        # --- azure.* ------------------------------------------------------
        if root == "azure":
            self._add_resource("cloud", "cloud")
            return

        # --- os.environ[...] is a Subscript, not a Call; see visit_Subscript
        # --- os.getenv(...) and os.environ.get(...) -----------------------
        if dotted in ("os.getenv", "os.environ.get"):
            arg = _first_string_arg(node)
            name = arg if arg else "credentials"
            self._add_resource(name, "credentials")
            self._add_op("read")
            return

        # --- dotenv.load_dotenv(...) --------------------------------------
        if dotted == "dotenv.load_dotenv" or leaf == "load_dotenv":
            self._add_resource("credentials", "credentials")
            self._add_op("read")
            return

        # --- stripe.* / paypal.* / payment / charge ----------------------
        if root in ("stripe", "paypal"):
            self._add_op("financial")
            return

        # --- chmod / chown ------------------------------------------------
        if dotted in ("os.chmod", "os.chown"):
            self._add_op("admin")
            return

        # --- .grant() (IAM-style) -----------------------------------------
        if leaf == "grant":
            self._add_op("admin")
            return

        # --- .read() (generic file/stream read) ---------------------------
        if leaf == "read":
            self._add_op("read")
            return

        # --- .write() (generic file/stream write) -------------------------
        if leaf == "write":
            self._add_op("write")
            return

    # ------------------------------------------------------------------
    # os.environ["KEY"] is a Subscript node, not a Call
    # ------------------------------------------------------------------

    def visit_Subscript(self, node):  # noqa: N802
        # Match os.environ[<key>]
        if isinstance(node.value, ast.Attribute):
            chain = self._attr_chain(node.value)
            if chain == ["os", "environ"]:
                # Extract key name
                key_node = node.slice
                # In Python 3.8 slices are wrapped in an Index node
                if isinstance(key_node, ast.Index):
                    key_node = key_node.value  # type: ignore[attr-defined]
                if isinstance(key_node, ast.Constant) and isinstance(
                    key_node.value, str
                ):
                    name = key_node.value
                else:
                    name = "credentials"
                self._add_resource(name, "credentials")
                self._add_op("read")
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # String constants — detect SQL keywords and payment keywords
    # ------------------------------------------------------------------

    def visit_Constant(self, node):  # noqa: N802
        if not isinstance(node.value, str):
            self.generic_visit(node)
            return
        upper = node.value.strip().upper()
        # Bare SQL keyword strings (not caught via .execute call)
        if re.match(r"^SELECT\b", upper):
            self._add_op("read")
        elif re.match(r"^(INSERT|UPDATE)\b", upper):
            self._add_op("write")
        elif re.match(r"^DELETE\b", upper):
            self._add_op("delete")
        # Payment keywords in any string literal
        if re.search(r"\bpayment\b|\bcharge\b", node.value, re.IGNORECASE):
            self._add_op("financial")
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Resource deduplication
# ---------------------------------------------------------------------------

def _dedup_resources(resources):
    """
    Drop generic fallback names when a specific name exists for the same type.

    Rule: within each resource type, if any entry has a name that differs from
    the type string itself, remove all entries whose name equals the type string.

    Example:
        [{"name": "customers", "type": "database"},
         {"name": "database",  "type": "database"}]
        →  [{"name": "customers", "type": "database"}]
    """
    from collections import defaultdict

    by_type = defaultdict(list)
    for r in resources:
        by_type[r["type"]].append(r)

    result = []
    for rtype, entries in by_type.items():
        specific = [e for e in entries if e["name"] != rtype]
        if specific:
            result.extend(specific)
        else:
            result.extend(entries)

    # Restore original insertion order as much as possible.
    order = {(r["name"], r["type"]): i for i, r in enumerate(resources)}
    result.sort(key=lambda r: order.get((r["name"], r["type"]), 0))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def infer_capabilities(scan_result: dict) -> dict:
    """
    Enrich each tool in *scan_result* with operation/resource inference.

    Returns the same dict structure as scan_repository(), with each tool
    entry augmented by:

        operation : str   — highest-severity operation detected
        resources : list  — [{name, type}, ...]
        inferred  : bool  — True if at least one resource was detected
    """
    enriched_tools = []

    for tool in scan_result.get("tools", []):
        source = tool.get("body_source", "")

        try:
            tree = ast.parse(source)
        except SyntaxError:
            enriched_tools.append({
                **tool,
                "operation": "read",
                "resources": [],
                "inferred": False,
            })
            continue

        visitor = _CapabilityVisitor()
        visitor.visit(tree)

        # Pick the highest-severity operation detected; default to "read"
        operation = "read"
        for op in visitor.operations:
            operation = _higher_op(operation, op)

        resources = _dedup_resources(visitor.resources)
        inferred = len(resources) > 0

        enriched_tools.append({
            **tool,
            "operation": operation,
            "resources": resources,
            "inferred": inferred,
        })

    return {**scan_result, "tools": enriched_tools}


# ---------------------------------------------------------------------------
# Manual smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    from . import scanner  # relative import when run as part of the package

    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "samples", "overprivileged_agent",
    )

    scan = scanner.scan_repository(sample_path)
    result = infer_capabilities(scan)

    print(f"Agent : {result['agent_name']}")
    print(f"Path  : {result['repo_path']}")
    print(f"Tools : {len(result['tools'])}\n")
    print("-" * 60)

    errors = []
    for t in result["tools"]:
        print(f"\n  {t['name']}  [{t['file']}:{t['lineno']}]")
        print(f"    operation : {t['operation']}")
        print(f"    inferred  : {t['inferred']}")
        if t["resources"]:
            for r in t["resources"]:
                print(f"    resource  : {r['name']}  ({r['type']})")
                # Verify: generic fallback name must not coexist with a
                # specific name of the same type.
                same_type = [x for x in t["resources"] if x["type"] == r["type"]]
                specific = [x for x in same_type if x["name"] != x["type"]]
                if specific and r["name"] == r["type"]:
                    errors.append(
                        f"FAIL [{t['name']}] generic '{r['name']}' "
                        f"coexists with specific names: "
                        f"{[x['name'] for x in specific]}"
                    )
        else:
            print("    resources : (none detected)")

    print()
    if errors:
        for msg in errors:
            print(msg)
    else:
        print("OK — no generic/specific duplicates found.")
