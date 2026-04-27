"""This file defines the grep tool, which searches for a regex pattern in files and returns matching lines while preventing unsafe path access."""

import re
import glob
import os
from tools.cat import is_path_safe


def grep(pattern, path):
    """Search for a regex pattern in files and return matching lines joined by newlines.

    >>> grep('hello', 'test_files/hello.txt')
    'hello world'

    >>> grep('NOTFOUND_XYZ', 'test_files/hello.txt')
    ''

    Only lines that match the pattern are returned.

    >>> grep('^hello', 'test_files/multiline.txt')
    'hello world'

    Searching a directory scans all files inside it; subdirectories are silently skipped.

    >>> grep('salve', 'test_files')
    'salve munde'

    Returns an empty string when the file does not exist.

    >>> grep('anything', 'nonexistent_file.txt')
    ''

    Does not support absolute paths or directory traversal.

    >>> grep('anything', '../')
    'Error: unsafe path'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    results = []

    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, "*"))
    else:
        files = glob.glob(path)

    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if re.search(pattern, line):
                        results.append(line.strip())
        except Exception:
            continue

    return "\n".join(results)


tool_schema = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": "Search for a regex pattern in files and return matching lines",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "The regex pattern to search for"},
                "path": {"type": "string", "description": "The file path or glob pattern to search"}
            },
            "required": ["pattern", "path"]
        }
    }
}
