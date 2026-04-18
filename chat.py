"""
This file defines the Chat class and REPL interface for interacting with the language model and available tools.
"""

from groq import Groq
from tools.calculate import calculate, tool_schema as calculate_schema
from tools.ls import ls, tool_schema as ls_schema
from tools.cat import cat, tool_schema as cat_schema
from tools.grep import grep, tool_schema as grep_schema
import json
from dotenv import load_dotenv


load_dotenv()

# in pytohn class names are in CamelCase;
# non-class names (e.g. functions/variables) are in snake_case
class Chat:
    """
    This class manages a conversation with a language model and integrates tool usage such as calculate, ls, cat, and grep.
    It maintains message history and handles tool calls automatically when the model requests them.

    >>> chat = Chat()
    >>> chat.send_message('my name is bob', temperature=0.0)  # doctest: +ELLIPSIS
    '...Bob...'
    >>> chat.send_message('what is my name?', temperature=0.0)  # doctest: +ELLIPSIS
    '...Bob...'

    >>> chat2 = Chat()
    >>> chat2.send_message('what is my name?', temperature=0.0)  # doctest: +ELLIPSIS
    '...name...'

    >>> chat = Chat()
    >>> "4" in chat.send_message('2+2', temperature=0.0)
    True
    """
    client = Groq()
    def __init__(self):
        """Initialize the chat with a default system prompt and empty message history."""
        self.MODEL = 'openai/gpt-oss-120b'
        self.messages = [
                {
                    # most important content for sys prompt is length of response
                    "role": "system",
                    "content": "Write the output in 1-2 sentences. Talk like pirate. Always use tools to complete tasks when appropriate"
                },
            ]
    def send_message(self, message, temperature=0.8):
        """
        Send a message to the language model, handle any tool calls, and return the model's response.

        >>> chat = Chat()
        >>> response = chat.send_message("2+2", temperature=0.0)
        >>> isinstance(response, str)
        True

        >>> chat = Chat()
        >>> initial_len = len(chat.messages)
        >>> _ = chat.send_message("hello", temperature=0.0)
        >>> len(chat.messages) > initial_len
        True

        >>> chat = Chat()
        >>> response = chat.send_message("say hi", temperature=0.0)
        >>> isinstance(response, str)
        True
        """
        self.messages.append(
            {
                # system: never change; user: changes a lot;
                # the message that you are sending to the AI
                'role': 'user',
                'content': message
            }
        )

        tools = [calculate_schema, ls_schema, cat_schema, grep_schema]
        # in order to make non-deterministic code deterministic;
        # in general very hard CS problem;
        # in this case, has a "temperature" param that controls randomness;
        # the higher the value, the more randomness;
        # hihgher temperature => more creativity
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
        
        # Step 2: Check if the model wants to call tools
        if tool_calls:
            # Map function names to implementations
            available_functions = {
                "calculate": calculate,
                "ls": ls,
                "cat": cat,
                "grep": grep,
            }
            
            # Add the assistant's response to conversation
            self.messages.append(response_message)
            
            # Step 3: Execute each tool call
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                
                
                # Add tool response to conversation
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # Step 4: Get final response from model
            second_response = self.client.chat.completions.create(
                model= self.MODEL,
                messages=self.messages,
                tools=tools,
                tool_choice="auto",
            )
            result = second_response.choices[0].message.content
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


def repl(temperature=0.8):
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
    ...
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

    chat = Chat()
    try:
        while True:
            user_input = input('chat> ')

            # handle slash commands
            if user_input.startswith("/"):
                if user_input == "/help":
                    print("Available commands: /help, /ls, /cat <file>, /grep <pattern> <path>, /calculate <expression>")

                elif user_input.startswith("/ls"):
                    parts = user_input.split()
                    path = parts[1] if len(parts) > 1 else "."
                    result = ls(path)
                    print(result)
                    chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/cat"):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("Usage: /cat <file>")
                    else:
                        result = cat(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                elif user_input.startswith("/grep"):
                    parts = user_input.split()
                    if len(parts) < 3:
                        print("Usage: /grep <pattern> <path>")
                    else:
                        result = grep(parts[1], parts[2])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})
                
                elif user_input.startswith("/calculate"):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("Usage: /calculate <expression>")
                    else:
                        result = calculate(parts[1])
                        print(result)
                        chat.messages.append({"role": "assistant", "content": result})

                else:
                    print("Unknown command")

                continue

            # normal chat
            response = chat.send_message(user_input, temperature)
            print(response)
    except (KeyboardInterrupt, EOFError):
        print()



if __name__ == '__main__':
    repl()
