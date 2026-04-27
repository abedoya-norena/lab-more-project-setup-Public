"""
This file defines the ls tool, which lists files in a directory and returns them as a sorted newline-separated string while preventing unsafe path access.
"""

import glob
import os

def is_path_safe(path):
    """
    Check whether a file path is safe by rejecting absolute paths and directory traversal.

    >>> is_path_safe("folder")
    True

    >>> is_path_safe("../secret")
    False

    >>> is_path_safe("/etc")
    False
    """
    return not (path.startswith("/") or ".." in path)


def ls(path="."):
    """
    List files in a directory and return them as a sorted newline-separated string.

    >>> ls("../")
    'Error: unsafe path'

    # once again, gross test case
    >>> isinstance(ls("nonexistent_dir_abc"), str)
    True

    >>> ls("nonexistent_dir_abc")
    ''
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    files = glob.glob(os.path.join(path, "*"))
    files = [os.path.basename(f) for f in files]

    return "\n".join(sorted(files))


tool_schema = {
    "type": "function",
    "function": {
        "name": "ls",
        "description": "List files in a directory and return them as a sorted newline-separated string",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The directory to list files from"}
            },
            "required": []
        }
    }
}
