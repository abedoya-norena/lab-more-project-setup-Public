"""This file defines the compact tool, which summarizes chat history into a short system message."""

import json


def _clean_messages(messages):
    """Convert a list of messages to plain dicts with role and content fields.

    ChatCompletionMessage objects (from the Groq SDK) are converted alongside plain dicts.

    >>> _clean_messages([{"role": "user", "content": "hello"}])
    [{'role': 'user', 'content': 'hello'}]

    >>> _clean_messages([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}])
    [{'role': 'user', 'content': 'hi'}, {'role': 'assistant', 'content': 'hello'}]
    """
    clean = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role", "")
            content = m.get("content", "")
        else:
            role = getattr(m, "role", "")
            content = getattr(m, "content", "")
        clean.append({"role": role, "content": content})
    return clean


def compact(messages):
    """Summarize a conversation history into 1-5 concise lines.

    Internally serializes the message list with _clean_messages, sends it to
    the LLM, and returns the summary string.  Because the LLM is
    nondeterministic, the output is not fixed; the helper _clean_messages is
    fully tested above.

    >>> _clean_messages([{"role": "user", "content": "ping"}])
    [{'role': 'user', 'content': 'ping'}]
    """
    from chat import Chat

    subagent = Chat()
    serialized = json.dumps(_clean_messages(messages), ensure_ascii=False)
    summary_request = (
        "Summarize this conversation in 1-5 concise lines. "
        "Capture only key context and decisions.\n\n"
        f"Conversation:\n{serialized}"
    )

    subagent.messages = [
        {
            "role": "system",
            "content": "You summarize conversations clearly and concisely in 1-5 lines.",
        },
        {"role": "user", "content": summary_request},
    ]

    completion = subagent.client.chat.completions.create(
        model=subagent.MODEL,
        messages=subagent.messages,
        temperature=0.2,
    )
    return (completion.choices[0].message.content or "").strip()


tool_schema = {
    "type": "function",
    "function": {
        "name": "compact",
        "description": "Summarize chat history into 1-5 concise lines for context compression",
        "parameters": {
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "description": "The current chat message history to summarize",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                }
            },
            "required": [],
        },
    },
}
