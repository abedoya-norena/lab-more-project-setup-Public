"""
This file defines the compact tool, which summarizes chat history into a short system message.
"""

import json


def compact(messages):
    # if you pass in the chat object here instead of messages,
    # you don't have to have the awkward special cases inside
    # the send_message function; you can do all that work here
    """
    Summarize a conversation history into 1-5 concise lines.

    >>> tool_schema["function"]["name"]
    'compact'
    """
    from chat import Chat

    subagent = Chat()
    clean_messages = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role", "")
            content = m.get("content", "")
        else:
            # handle ChatCompletionMessage objects
            role = getattr(m, "role", "")
            content = getattr(m, "content", "")
        clean_messages.append({"role": role, "content": content})

    serialized_messages = json.dumps(clean_messages, ensure_ascii=False)
    summary_request = (
        "Summarize this conversation in 1-5 concise lines. "
        "Capture only key context and decisions.\n\n"
        f"Conversation:\n{serialized_messages}"
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
