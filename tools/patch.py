"""Fuzzy unified-diff applicator that ignores incorrect line numbers.

LLMs reliably produce +/- content but routinely mis-count the @@ line numbers.
_apply_hunk ignores those numbers entirely and locates each hunk by fuzzy-
matching its context lines against the actual file content.
"""


def _parse_hunks(diff_text):
    """Split a unified diff string into a list of hunks.

    Each hunk is a list of (tag, line) pairs; tag is '+', '-', or ' '.
    File-header lines (--- / +++) and backslash lines are silently skipped.
    If no @@ markers appear the whole diff is treated as a single hunk.

    >>> _parse_hunks('@@ -1,3 +1,3 @@\\n a\\n-b\\n+B\\n c\\n')
    [[(' ', 'a'), ('-', 'b'), ('+', 'B'), (' ', 'c')]]

    >>> _parse_hunks('@@ -1 +1 @@\\n-x\\n+y\\n@@ -5 +5 @@\\n-p\\n+q\\n')
    [[('-', 'x'), ('+', 'y')], [('-', 'p'), ('+', 'q')]]

    Lines before the first @@ (file headers) are ignored.

    >>> _parse_hunks('--- a/f.py\\n+++ b/f.py\\n@@ -1 +1 @@\\n-a\\n+b\\n')
    [[('-', 'a'), ('+', 'b')]]

    --- and +++ lines that appear inside a hunk (after @@) are skipped.

    >>> _parse_hunks('@@ -1 +1 @@\\n--- a/f.py\\n+++ b/f.py\\n-x\\n+y\\n')
    [[('-', 'x'), ('+', 'y')]]

    Backslash continuation lines (e.g. \\ No newline at end of file) are skipped.

    >>> _parse_hunks('@@ -1 +1 @@\\n-x\\n\\\\ No newline at end of file\\n+y\\n')
    [[('-', 'x'), ('+', 'y')]]
    """
    hunks = []
    current = None
    for raw in diff_text.splitlines():
        if raw.startswith('@@'):
            if current is not None:
                hunks.append(current)
            current = []
        elif current is None:
            continue
        elif raw.startswith('+++') or raw.startswith('---'):
            continue
        elif raw.startswith('\\'):
            continue
        elif raw.startswith('+'):
            current.append(('+', raw[1:]))
        elif raw.startswith('-'):
            current.append(('-', raw[1:]))
        elif raw.startswith(' '):
            current.append((' ', raw[1:]))
    if current:
        hunks.append(current)
    return hunks


def _apply_hunk(file_lines, hunk):
    """Apply one hunk to file_lines and return the updated line list.

    The hunk is located by finding the window in file_lines whose stripped
    content best matches the context+removal lines.  Line-number metadata
    from the @@ header is never consulted.

    >>> _apply_hunk(['a', 'b', 'c'], [(' ', 'a'), ('-', 'b'), ('+', 'B'), (' ', 'c')])
    ['a', 'B', 'c']

    >>> _apply_hunk(['x', 'y', 'z'], [('-', 'y'), ('+', 'Y')])
    ['x', 'Y', 'z']

    Pure insertion: the context lines anchor the insertion point.

    >>> _apply_hunk(['a', 'b'], [(' ', 'a'), ('+', 'X'), (' ', 'b')])
    ['a', 'X', 'b']

    Pure deletion.

    >>> _apply_hunk(['a', 'b', 'c'], [(' ', 'a'), ('-', 'b'), (' ', 'c')])
    ['a', 'c']

    When the hunk has no context or removal lines, new lines are appended.

    >>> _apply_hunk([], [('+', 'first'), ('+', 'second')])
    ['first', 'second']
    """
    search = [line for tag, line in hunk if tag in (' ', '-')]
    replace = [line for tag, line in hunk if tag in (' ', '+')]

    if not search:
        return file_lines + [line for tag, line in hunk if tag == '+']

    n = len(search)
    best_score = -1
    best_i = 0

    for i in range(max(1, len(file_lines) - n + 1)):
        window = file_lines[i:i + n]
        score = sum(a.strip() == b.strip() for a, b in zip(window, search))
        if score > best_score:
            best_score = score
            best_i = i

    return file_lines[:best_i] + replace + file_lines[best_i + n:]


def apply_diff(original_content, diff_text):
    r"""Apply a unified diff to file content, tolerating wrong line numbers.

    Correct line numbers in the @@ header:

    >>> apply_diff('a\nb\nc\n', '@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n')
    'a\nB\nc\n'

    Wrong line numbers — fuzzy matching still finds the right location:

    >>> apply_diff('a\nb\nc\n', '@@ -99,3 +99,3 @@\n a\n-b\n+B\n c\n')
    'a\nB\nc\n'

    Insertion:

    >>> apply_diff('a\nb\n', '@@ -1,2 +1,3 @@\n a\n+X\n b\n')
    'a\nX\nb\n'

    Deletion:

    >>> apply_diff('a\nb\nc\n', '@@ -1,3 +1,2 @@\n a\n-b\n c\n')
    'a\nc\n'

    An empty diff leaves the content unchanged:

    >>> apply_diff('hello\n', '')
    'hello\n'
    """
    trailing_newline = original_content.endswith('\n')
    lines = original_content.split('\n')
    if trailing_newline:
        lines = lines[:-1]

    for hunk in _parse_hunks(diff_text):
        lines = _apply_hunk(lines, hunk)

    result = '\n'.join(lines)
    if trailing_newline:
        result += '\n'
    return result
