"""
This file defines the Chat class and REPL interface for interacting with the language model and available tools.

# this doctest didn't actually test anything about your code
"""

import argparse
import os
import readline
from groq import Groq
from tools.calculate import calculate, tool_schema as calculate_schema
from tools.ls import ls, tool_schema as ls_schema
from tools.cat import cat, tool_schema as cat_schema
from tools.grep import grep, tool_schema as grep_schema
from tools.compact import compact, tool_schema as compact_schema
import json
from dotenv import load_dotenv


load_dotenv()

# in python class names are in CamelCase;
# non-class names (e.g. functions/variables) are in snake_case
class Chat:
    """
    This class manages a conversation with a language model and integrates tool usage such as calculate, ls, cat, and grep.
    It maintains message history and handles tool calls automatically when the model requests them.

    # these are all decent tests
    >>> chat = Chat()
    >>> "Bob" in chat.send_message('my name is bob', temperature=0.0)
    True
    >>> "Bob" in chat.send_message('what is my name?', temperature=0.0)
    True

    >>> chat2 = Chat()
    >>> "name" in chat2.send_message('what is my name?', temperature=0.0)
    True

    >>> chat = Chat()
    >>> "4" in chat.send_message('2+2', temperature=0.0)
    True
    """
    client = Groq()
    def __init__(self, debug=False, provider="groq"):
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
            self.MODEL = "anthropic/claude-opus-4.1"
        elif provider == "google":
            self.MODEL = "google/gemini-2.0-flash-001"
        else:
            self.MODEL = "openai/gpt-oss-120b"
        self.debug = debug
        self.messages = [
                {
                    "role": "system",
                    "content": "Write the output in 1-2 sentences. Talk like pirate. Always use tools to complete tasks when appropriate"
                },
            ]

    def send_message(self, message, temperature=0.8):
        """
        Send a message to the language model, handle any tool calls, and return the model's response.

        # these test cases were not good;
        # they don't help me as a reader understand what your code
        # does, and just testing that the type is a string
        # is unlikely to catch any bugs;
        # the tests in the Chat docstring above are better
        """
        self.messages.append(
            {
                # system: never change; user: changes a lot;
                # the message that you are sending to the AI
                'role': 'user',
                'content': message
            }
        )

        tools = [calculate_schema, ls_schema, cat_schema, grep_schema, compact_schema]
        chat_completion = self.client.chat.completions.create(
            messages=self.messages,
            model= self.MODEL,
            temperature=temperature,
            seed=0,
            tools=tools,
            tool_choice="auto",
        )

        response_message = chat_completion.choices[0].message
        tool_calls = response_message.tool_calls

        # The Step annotations that you have here is the correct
        # style for annotating comments; I like to think of blocks
        # of code like "paragraphs" and the comments like
        # "topic sentences" that let me skim to see what I should
        # read/not read I've deleted a handful of "bad" comments
        # (that I realize you had because I typed it in lecture)
        # but these shouldn't make it into a "production" system
        # Step 2: Check if the model wants to call tools
        if tool_calls:
            # Map function names to implementations
            available_functions = {
                "calculate": calculate,
                "ls": ls,
                "cat": cat,
                "grep": grep,
                "compact": compact,
            }
            
            # Add the assistant's response to conversation
            self.messages.append(response_message)
            
            # Step 3: Execute each tool call
            compacted_summary = None
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                if function_name == "compact":
                    function_args = {"messages": self.messages}
                if self.debug:
                    print(f"[tool] /{function_name} {tool_call.function.arguments}")
                function_response = function_to_call(**function_args)

                # what you have here for the compact code is not
                # strictly "wrong", but it's a bit awkward to have
                # special cases for handling certain tools;
                # it would have been better if all this functionality
                # could have been handled within just the compact
                # tool, but that admittedly required some
                # out-of-the-box thinking
                if function_name == "compact":
                    self.messages = [{"role": "system", "content": function_response}]
                    compacted_summary = function_response
                    continue

                # Add tool response to conversation
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

            # Step 4: Get final response from model
            if compacted_summary is not None:
                result = compacted_summary
            else:
                second_response = self.client.chat.completions.create(
                    model= self.MODEL,
                    messages=self.messages,
                    tools=tools,
                    tool_choice="auto",
                )
                result = second_response.choices[0].message.content
            if compacted_summary is None:
                self.messages.append({
                    'role': 'assistant',
                    'content': result
                })
        else:
            result = chat_completion.choices[0].message.content
            self.messages.append({
                'role': 'assistant',
                'content': result
            })
        return result


def repl(temperature=0.8, debug=False, provider="groq"):
    """
    Run an interactive command-line chat loop that supports both natural language and slash commands.

    >>> def monkey_input(prompt, user_inputs=['Hello, I am monkey.', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> Hello, I am monkey.
    # these are not great test cases here because you are not
    # actually viewing the output of the code at all;
    # so what are you actually testing?
    # this one is admitedly hard to test because of nondeterminism
    # but that just means you probably shouldn't include the test;
    # the other tests that are testing your slash commands
    # are all deterministic and so the output should be directly
    # included
    chat> Goodbye.
    ...
    <BLANKLINE>

    >>> def monkey_input(prompt, user_inputs=['/ls .', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /ls .
    ...
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
    ...
    chat> Goodbye.
    ...
    <BLANKLINE>

    >>> def monkey_input(prompt, user_inputs=['/cat tools/cat.py', 'Goodbye.']):
    ...     try:
    ...         user_input = user_inputs.pop(0)
    ...         print(f'{prompt}{user_input}')
    ...         return user_input
    ...     except IndexError:
    ...         raise KeyboardInterrupt
    >>> import builtins
    >>> builtins.input = monkey_input
    >>> repl(temperature=0.0)  # doctest: +ELLIPSIS
    chat> /cat tools/cat.py
    ...
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
    ...
    chat> Goodbye.
    ...
    <BLANKLINE>
    """

    # it would be cleaner to build this directly from the tools;
    # possibly as a global that both locations can use
    commands = ["/ls", "/cat", "/grep", "/calculate", "/compact", "/help"]

    def completer(text, state):
        # this should have been a global function;
        # as a global function, you could have written test cases
        # these test cases not involve any io/non-determinism,
        # and so it would be easy to test and prove correct;
        # as a local function, there is no way for the reader
        # to understand what the function is doing or verify
        # it is correct
        line = readline.get_line_buffer()
        if not line.startswith("/"):
            matches = []
        elif " " not in line:
            matches = [cmd for cmd in commands if cmd.startswith(text)]
        else:
            arg = line.rsplit(" ", 1)[-1]
            matches = [name for name in os.listdir(".") if name.startswith(arg)]
        return matches[state] if state < len(matches) else None


    readline.set_completer_delims(" \t\n")
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    chat = Chat(debug=debug, provider=provider)
    try:
        while True:
            user_input = input('chat> ')

            # handle slash commands
            if user_input.startswith("/"):
                if user_input == "/help":
                    print("Available commands: /help, /ls, /cat <file>, /grep <pattern> <path>, /calculate <expression>, /compact")

                # it's not "wrong" to have separate if
                # statements for all of your commands,
                # but it duplicates a lot of code and makes
                # adding new commands a bit of a chore;
                # it would be possible to factor this all out
                # (and I believe the groq docs have examples)
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
                    summary = compact(chat.messages)
                    chat.messages = [{"role": "system", "content": summary}]
                    print(summary)

                else:
                    print("Unknown command")

                continue

            # normal chat
            response = chat.send_message(user_input, temperature)
            print(response)
    except (KeyboardInterrupt, EOFError):
        print()

# none of these functions were doing anything;
# and the doctests were not actually testing your code;
# we call this "dead code" and it should always be removed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--provider", default="groq")
    parser.add_argument("message", nargs="*", help="Optional message")

    args = parser.parse_args()

    if args.message:
        chat = Chat(debug=args.debug, provider=args.provider)
        print(chat.send_message(" ".join(args.message)))
    else:
        repl(debug=args.debug, provider=args.provider)
