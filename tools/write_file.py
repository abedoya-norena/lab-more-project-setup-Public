"""This file defines the write_file tool, a thin wrapper around write_files that also runs doctests on Python files."""

from tools.write_files import write_files
from tools.doctests import run_doctests
from tools.cat import is_path_safe


def write_file(path, commit_message, contents=None, diff=None):
    """Write or patch a single file, commit it, and run doctests if it is a Python file.

    Pass 'contents' to write the full file text, or 'diff' to apply a unified
    diff to the existing file.  Exactly one of the two must be provided.

    Does not support absolute paths or directory traversal.

    >>> write_file('/etc/passwd', 'test', contents='bad')
    "Error: unsafe path '/etc/passwd'"

    >>> write_file('../secret.py', 'test', contents='bad')
    "Error: unsafe path '../secret.py'"

    >>> write_file('f.txt', 'test')
    "Error: must provide 'contents' or 'diff'"
    """
    if not is_path_safe(path):
        return f"Error: unsafe path '{path}'"
    if contents is None and diff is None:
        return "Error: must provide 'contents' or 'diff'"

    entry = {'path': path}
    if diff is not None and contents is None:
        entry['diff'] = diff
    else:
        entry['contents'] = contents

    result = write_files([entry], commit_message)
    if result.startswith('Error'):
        return result
    if path.endswith('.py'):
        doctest_output = run_doctests(path)
        return f"{result}\n\nDoctest results:\n{doctest_output}"
    return result


tool_schema = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write or patch a single file, commit it, and run doctests if it is a Python file. "
            "Pass 'contents' for a full rewrite (new files or complete replacements) or 'diff' "
            "to apply a unified diff to an existing file (efficient for large files). "
            "Exactly one of the two must be supplied."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write or patch"},
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message (prefixed with [docchat])"
                },
                "contents": {
                    "type": "string",
                    "description": "Full UTF-8 content to write (use for new files or complete rewrites)"
                },
                "diff": {
                    "type": "string",
                    "description": (
                        "Unified diff to apply to the existing file (use for partial updates). "
                        "Wrong line numbers in @@ headers are tolerated — context lines are "
                        "used for fuzzy matching."
                    )
                },
            },
            "required": ["path", "commit_message"]
        }
    }
}
