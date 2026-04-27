"""This file defines the Chat class and REPL interface for interacting with the language model and available tools."""

import argparse
import os
import sys
try:
    import readline
except ImportError:
    readline = None
from groq import Groq
from tools.calculate import calculate, tool_schema as calculate_schema
from tools.ls import ls, tool_schema as ls_schema
from tools.cat import cat, tool_schema as cat_schema
from tools.grep import grep, tool_schema as grep_schema
from tools.compact import compact, tool_schema as compact_schema
from tools.doctests import run_doctests, tool_schema as doctests_schema
from tools.write_file import write_file, tool_schema as write_file_schema
from tools.write_files import write_files, tool_schema as write_files_schema
from tools.rm import rm, tool_schema as rm_schema
from tools.pip_install import pip_install, tool_schema as pip_install_schema
from tools.load_image import load_image, tool_schema as load_image_schema
import json
from dotenv import load_dotenv


load_dotenv()

TOOLS = [
    calculate_schema, ls_schema, cat_schema, grep_schema, compact_schema,
    doctests_schema, write_file_schema, write_files_schema, rm_schema,
    pip_install_schema, load_image_schema,
]

AVAILABLE_FUNCTIONS = {
    "calculate": calculate,
    "ls": ls,
    "cat": cat,
    "grep": grep,
    "compact": compact,
    "run_doctests": run_doctests,
    "write_file": write_file,
    "write_files": write_files,
    "rm": rm,
    "pip_install": pip_install,
    "load_image": load_image,
}


class Chat:
    """Manage a conversation with a language model and integrate tool usage such as calculate, ls, cat, grep, write_file, and rm.

    Maintains message history and handles tool calls automatically when the model requests them.

    Because LLMs are nondeterministic, the doctests below do not check the full response.
    We assert that the model's reply contains the expected name or value.

    >>> chat = Chat()
    >>> 'Bob' in chat.send_message('my name is bob', temperature=0.0)
    True
    >>> 'Bob' in chat.send_message('what is my name?', temperature=0.0)
    True

    A second Chat instance has no memory of the first conversation.

    >>> chat2 = Chat()
    >>> 'Bob' in chat2.send_message('what is my name?', temperature=0.0)
    False

    The model uses the calculate tool when given arithmetic.

    >>> chat3 = Chat()
    >>> '4' in chat3.send_message('what is 2+2?', temperature=0.0)
    True
    """

    client = Groq()

    def __init__(self, debug=False, provider="groq", ralph=True):
        """Initialize the chat with a default system prompt and empty message history."""
        self.provider = provider
        if provider == "groq":
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        else:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        if provider == "openai":
            self.MODEL = "openai/gpt-4o"
        elif provider == "anthropic":
            self.MODEL = "anthropic/claude-opus-4-5"
        elif provider == "google":
            self.MODEL = "google/gemini-2.0-flash-001"
        else:
            self.MODEL = "openai/gpt-oss-120b"
        self.debug = debug
        self.ralph = ralph
        self.messages = [
            {
                "role": "system",
                "content": "Write the output in 1-2 sentences. Talk like pirate. Always use tools to complete tasks when appropriate"
            },
        ]

    def send_message(self, message, temperature=0.8):
        """Send a message to the language model, handle any tool calls, and return the model's response.

        When ralph=True (the default), any write_file call whose doctests fail causes the agent
        to loop: the failure output is fed back as a user message and the model is asked to fix
        the code and try again.  The loop repeats until doctests pass or the model stops calling
        tools.
        """
        self.messages.append({'role': 'user', 'content': message})

        while True:
            response = self.client.chat.completions.create(
                messages=self.messages,
                model=self.MODEL,
                temperature=temperature,
                seed=0,
                tools=TOOLS,
                tool_choice="auto",
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                result = response_message.content
                self.messages.append({'role': 'assistant', 'content': result})
                return result

            self.messages.append(response_message)

            compacted_summary = None
            doctest_failed = False
            images_to_inject = []

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = AVAILABLE_FUNCTIONS[function_name]
                function_args = json.loads(tool_call.function.arguments)
                if function_name == "compact":
                    function_args = {"messages": self.messages}
                if self.debug:
                    print(f"[tool] /{function_name} {tool_call.function.arguments}")
                function_response = function_to_call(**function_args)

                if function_name == "compact":
                    self.messages = [{"role": "system", "content": function_response}]
                    compacted_summary = function_response
                    continue

                if function_name == "load_image":
                    if function_response.startswith("Error"):
                        tool_content = function_response
                    else:
                        images_to_inject.append(function_response)
                        tool_content = f"Image '{function_args.get('path', '')}' loaded into context."
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_content,
                    })
                    continue

                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

                if self.ralph and "Test Failed" in function_response:
                    doctest_failed = True

            for url in images_to_inject:
                self.messages.append({
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": {"url": url}}],
                })

            if compacted_summary is not None:
                return compacted_summary

            if doctest_failed:
                if self.debug:
                    print("[ralph] doctests failed — asking model to fix and retry")
                self.messages.append({
                    "role": "user",
                    "content": "The doctests failed. Please fix the code and try again.",
                })


def load_agents_md(chat):
    """Load AGENTS.md into the chat context if it exists in the current directory.

    >>> chat = Chat.__new__(Chat)
    >>> chat.messages = []
    >>> load_agents_md(chat)
    >>> chat.messages
    []
    """
    if os.path.exists('AGENTS.md'):
        content = cat('AGENTS.md')
        chat.messages.append({
            "role": "user",
            "content": f"[AGENTS.md — project instructions for AI agents]:\n{content}"
        })


def completer(text, state, commands=None, line=None):
    """Return the state-th tab-completion match for text given the current readline buffer.

    Commands are completed when the input starts with '/'; otherwise filenames are completed.
    Pass ``line`` explicitly in tests; when called by readline it is read from the buffer.

    >>> completer('/l', 0, commands=['/ls', '/cat', '/calculate'], line='/l')
    '/ls'

    >>> completer('/c', 0, commands=['/ls', '/cat', '/calculate'], line='/c')
    '/cat'

    >>> completer('/c', 1, commands=['/ls', '/cat', '/calculate'], line='/c')
    '/calculate'

    >>> completer('/z', 0, commands=['/ls', '/cat'], line='/z') is None
    True
    """
    if commands is None:
        commands = ["/ls", "/cat", "/grep", "/calculate", "/compact", "/help",
                    "/doctests", "/rm", "/pip_install", "/load_image"]
    if line is None:
        line = readline.get_line_buffer() if readline else ""
    if not line.startswith("/"):
        matches = []
    elif " " not in line:
        matches = [cmd for cmd in commands if cmd.startswith(text)]
    else:
        arg = line.rsplit(" ", 1)[-1]
        matches = [name for name in os.listdir(".") if name.startswith(arg)]
    return matches[state] if state < len(matches) else None


def repl(temperature=0.8, debug=False, provider="groq", ralph=True):
    """Run an interactive command-line chat loop that supports both natural language and slash commands.

    Slash commands run tools directly without an LLM call, giving instant deterministic output.
    The LLM is only invoked for natural-language messages.

    Exits with an error if the current directory is not a git repository.

    >>> def monkey_input(prompt, user_inputs=['/ls test_files', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /ls test_files
    hello.txt
    multiline.txt
    subdir
    chat> Goodbye.
    ...
    <BLANKLINE>

    >>> def monkey_input(prompt, user_inputs=['/calculate 2+2', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /calculate 2+2
    {"result": 4}
    chat> Goodbye.
    ...
    <BLANKLINE>

    >>> def monkey_input(prompt, user_inputs=['/cat test_files/hello.txt', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /cat test_files/hello.txt
    hello world
    chat> Goodbye.
    ...
    <BLANKLINE>

    >>> def monkey_input(prompt, user_inputs=['/help', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /help
    Available commands: /help, /ls, /cat <file>, /grep <pattern> <path>, /calculate <expression>, /compact, /doctests <file>, /rm <path>, /pip_install <library>
    chat> Goodbye.
    ...
    <BLANKLINE>
    """
    if not os.path.exists('.git'):
        print("Error: not a git repository. Please run chat from within a git repo.")
        return

    commands = ["/ls", "/cat", "/grep", "/calculate", "/compact", "/help",
                "/doctests", "/rm", "/pip_install", "/load_image"]

    if readline:
        readline.set_completer_delims(" \t\n")
        readline.set_completer(lambda text, state: completer(text, state, commands))
        readline.parse_and_bind("tab: complete")

    chat = Chat(debug=debug, provider=provider, ralph=ralph)
    load_agents_md(chat)

    try:
        while True:
            user_input = input('chat> ')

            if user_input.startswith("/"):
                if user_input == "/help":
                    print("Available commands: /help, /ls, /cat <file>, /grep <pattern> <path>, /calculate <expression>, /compact, /doctests <file>, /rm <path>, /pip_install <library>, /load_image <path>")

                elif user_input.startswith("/ls"):
                    parts = user_input.split()
                    path = parts[1] if len(parts) > 1 else "."
                    if debug:
                        print(f"[tool] /ls {path}", flush=True)
                    result = ls(path)
                    print(result)
                    chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/cat"):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("Usage: /cat <file>")
                    else:
                        if debug:
                            print(f"[tool] /cat {parts[1]}", flush=True)
                        result = cat(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/grep"):
                    parts = user_input.split()
                    if len(parts) < 3:
                        print("Usage: /grep <pattern> <path>")
                    else:
                        if debug:
                            print(f"[tool] /grep {parts[1]} {parts[2]}", flush=True)
                        result = grep(parts[1], parts[2])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/calculate"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Usage: /calculate <expression>")
                    else:
                        if debug:
                            print(f"[tool] /calculate {parts[1]}", flush=True)
                        result = calculate(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/compact"):
                    if debug:
                        print("[tool] /compact", flush=True)
                    try:
                        summary = compact(chat.messages)
                        chat.messages = [{"role": "system", "content": summary}]
                        print(summary)
                    except Exception as e:
                        print(f"Error running compact: {e}")

                elif user_input.startswith("/doctests"):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("Usage: /doctests <file>")
                    else:
                        if debug:
                            print(f"[tool] /doctests {parts[1]}", flush=True)
                        result = run_doctests(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/rm"):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("Usage: /rm <path>")
                    else:
                        if debug:
                            print(f"[tool] /rm {parts[1]}", flush=True)
                        result = rm(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/pip_install"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Usage: /pip_install <library_name>")
                    else:
                        if debug:
                            print(f"[tool] /pip_install {parts[1]}", flush=True)
                        result = pip_install(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/load_image"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Usage: /load_image <path>")
                    else:
                        if debug:
                            print(f"[tool] /load_image {parts[1]}", flush=True)
                        result = load_image(parts[1])
                        if result.startswith("Error"):
                            print(result)
                        else:
                            chat.messages.append({
                                "role": "user",
                                "content": [{"type": "image_url", "image_url": {"url": result}}],
                            })
                            print(f"Image '{parts[1]}' loaded into context.")

                else:
                    print("Unknown command")

                continue

            response = chat.send_message(user_input, temperature)
            print(response)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--provider", default="groq")
    parser.add_argument("--no-ralph", action="store_true", default=False,
                        help="Disable the Ralph Wiggum doctest retry loop")
    parser.add_argument("message", nargs="*", help="Optional message")

    args = parser.parse_args()
    ralph = not args.no_ralph

    if not os.path.exists('.git'):
        print("Error: not a git repository. Please run chat from within a git repo.")
        sys.exit(1)

    if args.message:
        chat = Chat(debug=args.debug, provider=args.provider, ralph=ralph)
        load_agents_md(chat)
        print(chat.send_message(" ".join(args.message)))
    else:
        repl(debug=args.debug, provider=args.provider, ralph=ralph)
