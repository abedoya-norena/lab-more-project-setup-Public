"""This file defines the load_image tool, which encodes a local image as a base64 data URL.

The tool returns the data URL string.  send_message detects this tool by name and injects
a multimodal user message into Chat.messages so the vision model can see the image.
"""

import base64
import mimetypes
from tools.cat import is_path_safe

SUPPORTED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


def load_image(path):
    """Read a local image file and return it as a base64 data URL.

    The caller (send_message or the REPL) is responsible for injecting the
    returned URL into the Chat.messages list as a multimodal user message.

    Does not support absolute paths or directory traversal.

    >>> load_image('/etc/passwd')
    'Error: unsafe path'

    >>> load_image('../secret.png')
    'Error: unsafe path'

    >>> load_image('test_files/does_not_exist.png')
    'Error: file not found'

    >>> load_image('test_files/hello.txt')
    'Error: unsupported image type (text/plain)'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    mime_type, _ = mimetypes.guess_type(path)
    if mime_type not in SUPPORTED_MIME_TYPES:
        return f"Error: unsupported image type ({mime_type})"

    try:
        with open(path, 'rb') as f:
            data = base64.standard_b64encode(f.read()).decode('ascii')
        return f"data:{mime_type};base64,{data}"
    except FileNotFoundError:
        return "Error: file not found"
    except Exception as e:
        return f"Error: {e}"


tool_schema = {
    "type": "function",
    "function": {
        "name": "load_image",
        "description": (
            "Load a local image file (JPEG, PNG, GIF, or WebP) into the conversation so the "
            "vision model can see it. Call this before asking questions about the image. "
            "Requires a vision-capable model."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the image file"}
            },
            "required": ["path"]
        }
    }
}
