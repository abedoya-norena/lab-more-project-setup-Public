"""This file defines the write_files tool, which writes multiple files and commits them to git."""

import os
import git
from tools.cat import is_path_safe


def write_files(files, commit_message):
    """Write multiple files (utf-8) and commit them with a [docchat] prefix.

    Does not support absolute paths or directory traversal.

    >>> write_files([{'path': '/etc/passwd', 'contents': 'bad'}], 'test')
    "Error: unsafe path '/etc/passwd'"

    >>> write_files([{'path': '../secret.txt', 'contents': 'bad'}], 'test')
    "Error: unsafe path '../secret.txt'"
    """
    for f in files:
        path = f['path']
        if not is_path_safe(path):
            return f"Error: unsafe path '{path}'"
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(f['contents'])

    paths = [f['path'] for f in files]
    repo = git.Repo('.')
    repo.git.add(*paths)
    try:
        repo.git.commit('-m', f'[docchat] {commit_message}')
        return f"Wrote {len(files)} file(s) and committed: [docchat] {commit_message}"
    except git.exc.GitCommandError:
        return f"Wrote {len(files)} file(s) (no changes to commit)"


tool_schema = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": "Write multiple files (utf-8 encoded) and commit them to git",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of files to write",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to write"},
                            "contents": {"type": "string", "description": "UTF-8 content to write"}
                        },
                        "required": ["path", "contents"]
                    }
                },
                "commit_message": {"type": "string", "description": "Git commit message (prefixed with [docchat])"}
            },
            "required": ["files", "commit_message"]
        }
    }
}
