"""This file defines the cat tool, which reads the contents of a file and returns it as a string while preventing unsafe path access."""


def is_path_safe(path):
    """Check whether a file path is safe by rejecting absolute paths and directory traversal.

    >>> is_path_safe("file.txt")
    True

    >>> is_path_safe("../secret.txt")
    False

    >>> is_path_safe("/etc/passwd")
    False
    """
    return not (path.startswith("/") or ".." in path)


def cat(path):
    r"""Return the contents of a text file, or an error string if the file cannot be read.

    >>> cat('test_files/hello.txt')
    'hello world'

    >>> print(cat('test_files/multiline.txt'))
    hello world
    hola mundo
    salve munde

    Returns an error when the file does not exist.

    >>> cat('test_files/does_not_exist.txt')
    'Error: file not found'

    Returns an error when the path is a directory.

    >>> cat('.')
    'Error: could not read file'

    Does not support absolute paths or directory traversal.

    >>> cat('/etc/passwd')
    'Error: unsafe path'

    >>> cat('../secret.txt')
    'Error: unsafe path'
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
