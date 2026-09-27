from pathlib import Path
from langchain.tools import tool


@tool
def read_docs(path: str) -> str:
    """Read public documentation files from the docs directory."""
    docs_root = Path("/workspace/docs")
    target = docs_root / path
    return target.read_text()