"""This file defines the rm tool, which deletes files matching a glob pattern and commits the removal."""

import os
import glob
import git
from tools.cat import is_path_safe


def rm(path):
    """Delete all files matching a glob pattern and commit the removal.

    Does not support absolute paths or directory traversal.

    >>> rm('/etc/passwd')
    'Error: unsafe path'

    >>> rm('../secret.txt')
    'Error: unsafe path'

    Returns an error when no files match the pattern.

    >>> rm('test_files/does_not_exist_xyz_123.txt')
    'Error: no files found matching test_files/does_not_exist_xyz_123.txt'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    files = glob.glob(path)
    if not files:
        return f"Error: no files found matching {path}"

    for f in files:
        os.remove(f)

    repo = git.Repo('.')
    repo.git.add(*files)
    repo.git.commit('-m', f'[docchat] rm {path}')

    return f"Removed {len(files)} file(s): {', '.join(sorted(files))}"


tool_schema = {
    "type": "function",
    "function": {
        "name": "rm",
        "description": "Delete files matching a glob pattern and commit the removal",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path or glob pattern to delete"}
            },
            "required": ["path"]
        }
    }
}
