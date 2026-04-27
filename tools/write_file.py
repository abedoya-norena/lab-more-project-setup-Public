"""This file defines the write_file tool, a thin wrapper around write_files that also runs doctests on Python files."""

from tools.write_files import write_files
from tools.doctests import run_doctests
from tools.cat import is_path_safe


def write_file(path, contents, commit_message):
    """Write a single file, commit it, and run doctests if it is a Python file.

    Does not support absolute paths or directory traversal.

    >>> write_file('/etc/passwd', 'bad', 'test')
    "Error: unsafe path '/etc/passwd'"

    >>> write_file('../secret.py', 'bad', 'test')
    "Error: unsafe path '../secret.py'"
    """
    result = write_files([{'path': path, 'contents': contents}], commit_message)
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
        "description": "Write a single file (utf-8 encoded), commit it, and run doctests if it is a Python file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "contents": {"type": "string", "description": "UTF-8 content to write"},
                "commit_message": {"type": "string", "description": "Git commit message (prefixed with [docchat])"}
            },
            "required": ["path", "contents", "commit_message"]
        }
    }
}
