from pathlib import Path
from langchain.tools import tool


@tool
def read_file(path: str) -> str:
    """Read a file from the filesystem."""
    return Path(path).read_text()


@tool
def write_file(path: str, content: str) -> bool:
    """Write content to a file on the filesystem."""
    Path(path).write_text(content)
    return True