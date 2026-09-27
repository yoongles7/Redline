import subprocess
from langchain.tools import tool


@tool
def run_shell(command: str) -> str:
    """Execute a shell command on the host system."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout