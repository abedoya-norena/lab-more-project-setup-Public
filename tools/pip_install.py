"""This file defines the pip_install tool, which installs a PyPI package.

WARNING: PyPI packages can execute arbitrary code at install time. Only install
packages you trust. This tool gives the agent the ability to run arbitrary code
on your machine.
"""

import re
import subprocess
import sys


def pip_install(library_name):
    """Install a PyPI package and return the pip output.

    Only package names matching the PyPI naming convention are accepted
    (letters, digits, hyphens, underscores, dots, and an optional version
    specifier like ==1.2.3). This prevents shell injection via the library name.

    >>> pip_install('requests; rm -rf /')
    'Error: invalid package name'

    >>> pip_install('../evil')
    'Error: invalid package name'

    >>> pip_install('')
    'Error: invalid package name'
    """
    if not re.fullmatch(r'[A-Za-z0-9_.\-]+([=<>!~][A-Za-z0-9_.\-,*]+)?', library_name):
        return "Error: invalid package name"

    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', library_name],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


tool_schema = {
    "type": "function",
    "function": {
        "name": "pip_install",
        "description": "Install a Python package from PyPI using pip. WARNING: packages can execute arbitrary code at install time.",
        "parameters": {
            "type": "object",
            "properties": {
                "library_name": {
                    "type": "string",
                    "description": "The PyPI package name to install, e.g. 'requests' or 'numpy==1.26.0'"
                }
            },
            "required": ["library_name"]
        }
    }
}
