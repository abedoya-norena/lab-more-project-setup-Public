"""This file defines the write_files tool, which writes multiple files and commits them to git."""

import os
import git
from tools.cat import is_path_safe, cat
from tools.patch import apply_diff


def write_files(files, commit_message):
    """Write (or patch) multiple files and commit them with a [docchat] prefix.

    Each entry in files must have a 'path' and either 'contents' (full text to
    write) or 'diff' (unified diff to apply to the existing file).

    Does not support absolute paths or directory traversal.

    >>> write_files([{'path': '/etc/passwd', 'contents': 'bad'}], 'test')
    "Error: unsafe path '/etc/passwd'"

    >>> write_files([{'path': '../secret.txt', 'contents': 'bad'}], 'test')
    "Error: unsafe path '../secret.txt'"

    >>> write_files([{'path': 'nofile.txt', 'diff': '@@ -1 +1 @@\\n-x\\n+y\\n'}], 't')
    "Error: cannot apply diff to 'nofile.txt': file not found"
    """
    resolved = []
    for f in files:
        path = f['path']
        if not is_path_safe(path):
            return f"Error: unsafe path '{path}'"

        if 'diff' in f and 'contents' not in f:
            existing = cat(path)
            if existing.startswith('Error:'):
                return f"Error: cannot apply diff to '{path}': {existing[len('Error: '):]}"
            contents = apply_diff(existing, f['diff'])
        elif 'contents' in f:
            contents = f['contents']
        else:
            return f"Error: file entry for '{path}' must have 'contents' or 'diff'"

        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write(contents)
        resolved.append(path)

    repo = git.Repo('.')
    repo.git.add(*resolved)
    try:
        repo.git.commit('-m', f'[docchat] {commit_message}')
        return f"Wrote {len(resolved)} file(s) and committed: [docchat] {commit_message}"
    except git.exc.GitCommandError:
        return f"Wrote {len(resolved)} file(s) (no changes to commit)"


tool_schema = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": (
            "Write or patch multiple files and commit them to git. "
            "Each file entry needs 'path' and either 'contents' (full text, for new files "
            "or complete rewrites) or 'diff' (unified diff, for partial updates to existing "
            "files). Diffs are applied with fuzzy matching so incorrect @@ line numbers are "
            "tolerated."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of files to write or patch",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "contents": {
                                "type": "string",
                                "description": "Full UTF-8 content to write (for new files or rewrites)"
                            },
                            "diff": {
                                "type": "string",
                                "description": (
                                    "Unified diff to apply to the existing file (for partial updates). "
                                    "Wrong line numbers in @@ headers are tolerated."
                                )
                            },
                        },
                        "required": ["path"]
                    }
                },
                "commit_message": {
                    "type": "string",
                    "description": "Git commit message (prefixed with [docchat])"
                }
            },
            "required": ["files", "commit_message"]
        }
    }
}
