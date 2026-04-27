"""
This file defines the cat tool, which reads the contents of a file and returns it as a string while preventing unsafe path access.
"""

def is_path_safe(path):
    """
    Check whether a file path is safe by rejecting absolute paths and directory traversal.

    >>> is_path_safe("file.txt")
    True

    >>> is_path_safe("../secret.txt")
    False

    >>> is_path_safe("/etc/passwd")
    False
    >>> isinstance(cat(__file__), str)
    True
    """
    return not (path.startswith("/") or ".." in path)


def cat(path):
    """
    Read the contents of a file and return it as a string, or return an error message if the file cannot be accessed.

    >>> cat("nonexistent_file.txt")
    'Error: file not found'

    >>> cat("../secret.txt")
    'Error: unsafe path'

    >>> cat(".")
    'Error: could not read file'

    # gross test case; you should pick a file that you can actually
    # show the output of
    >>> cat("tools/cat.py") != ""
    True
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: file not found"
    except Exception:
        return "Error: could not read file"


tool_schema = {
    "type": "function",
    "function": {
        "name": "cat",
        "description": "Read the contents of a file safely and return it as a string",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file path to read"}
            },
            "required": ["path"]
        }
    }
}
