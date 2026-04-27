"""This file defines the run_doctests tool, which runs doctests on a file and returns the output."""

import subprocess
import sys
from tools.cat import is_path_safe


def run_doctests(path):
    r"""Run doctests with verbose output on a file and return the combined stdout/stderr.

    Does not support absolute paths or directory traversal.

    >>> run_doctests('/etc/passwd')
    'Error: unsafe path'

    >>> run_doctests('../secret.py')
    'Error: unsafe path'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    result = subprocess.run(
        [sys.executable, '-m', 'doctest', '-v', path],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


tool_schema = {
    "type": "function",
    "function": {
        "name": "run_doctests",
        "description": "Run doctests with verbose output on a Python file and return the results",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the Python file to test"}
            },
            "required": ["path"]
        }
    }
}
