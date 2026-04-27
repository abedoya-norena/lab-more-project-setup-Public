"""This file defines the ls tool, which lists files in a directory and returns them as a sorted newline-separated string while preventing unsafe path access."""

import glob
import os
from tools.cat import is_path_safe


def ls(path="."):
    """List files in a directory and return them as a sorted newline-separated string.

    >>> ls('test_files')
    'hello.txt\\nmultiline.txt\\nsubdir'

    Returns an empty string when the directory does not exist.

    >>> ls('nonexistent_dir_abc')
    ''

    Does not support absolute paths or directory traversal.

    >>> ls('../')
    'Error: unsafe path'

    >>> ls('/etc')
    'Error: unsafe path'
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
