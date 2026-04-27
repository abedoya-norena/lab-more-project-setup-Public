"""
This file defines the grep tool, which searches for a regex pattern in files and returns matching lines while preventing unsafe path access.
"""

import re
import glob
import os
from tools.cat import is_path_safe
# it's very ugly to have the same function duplicated in multiple
# files; you can just import the function

def grep(pattern, path):
    """
    Search for a regex pattern in files and return matching lines joined by newlines.

    >>> grep("anything", "../")
    'Error: unsafe path'

    >>> grep("THIS_WILL_NOT_MATCH_123", "nonexistent_file.txt")
    ''

    # these test cases are gross; grep is fully deterministic
    # and so there is no reason not to put the actual output
    # of your functions here
    >>> isinstance(grep("pattern", "nonexistent_file.txt"), str)
    True

    >>> isinstance(grep("test", "."), str)
    True

    >>> isinstance(grep(".*", __file__), str)
    True
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
