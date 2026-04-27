# in general, I strongly discourage putting tests in separate files
# instead of in doctests; one of the major points of testing
# is to help ensure that the reader understand the purpose of a 
# function, and if you bury the tests in these other files,
# then the reader will have no idea where to look for the tests;
# keeping tests close to their source code is doubly important
# in the age of AI because if you are asking an AI to work on 
# a function, you want the AI to know what the test cases are
# for the function as well
import types
import subprocess
import os
import chat


class _FakeGroq:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        message = types.SimpleNamespace(tool_calls=None, content="stubbed response")
        choice = types.SimpleNamespace(message=message)
        return types.SimpleNamespace(choices=[choice])


class _ToolCall:
    def __init__(self, name, arguments, tool_id="tool_1"):
        self.function = types.SimpleNamespace(name=name, arguments=arguments)
        self.id = tool_id


def _response_with_tool_calls(tool_calls):
    message = types.SimpleNamespace(tool_calls=tool_calls, content=None)
    choice = types.SimpleNamespace(message=message)
    return types.SimpleNamespace(choices=[choice])


def test_send_message_compact_tool_call_debug(monkeypatch, capsys):
    chat_instance = chat.Chat(debug=True)

    calls = [_response_with_tool_calls([_ToolCall("compact", "{}")])]

    def fake_create(**kwargs):
        return calls.pop(0)

    monkeypatch.setattr(chat_instance.client.chat.completions, "create", fake_create)
    monkeypatch.setattr(chat, "compact", lambda messages: "condensed summary")

    result = chat_instance.send_message("please compact this", temperature=0.0)
    output = capsys.readouterr().out

    assert "[tool] /compact {}" in output
    assert result == "condensed summary"
    assert chat_instance.messages == [{"role": "system", "content": result}]


def test_repl_slash_command_branches_with_debug(monkeypatch, capsys):
    inputs = iter(
        [
            "/ls .",
            "/cat",
            "/cat chat.py",
            "/grep",
            "/grep Chat chat.py",
            "/calculate",
            "/calculate 3*3",
            "/compact",
            "/unknown",
        ]
    )

    def fake_input(prompt):
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(chat, "compact", lambda messages: "short context")

    chat.repl(debug=True)
    output = capsys.readouterr().out

    assert "[tool] /ls ." in output
    assert "Usage: /cat <file>" in output
    assert "[tool] /cat chat.py" in output
    assert "Usage: /grep <pattern> <path>" in output
    assert "[tool] /grep Chat chat.py" in output
    assert "Usage: /calculate <expression>" in output
    assert "[tool] /calculate 3*3" in output
    assert "[tool] /compact" in output
    assert "short context" in output
    assert "Unknown command" in output


def test_main_entrypoint_with_and_without_message():
    env = os.environ.copy()
    env["GROQ_API_KEY"] = "test"

    # Case 1: no message (REPL exits immediately)
    # anytime you are tempted to use subprocess.run in a test case
    # this should really be in a shell script;
    # (subprocess.run invokes a shell to run the command)
    # "integration tests" are the only reason to use separate
    # files in this style, and at least for this assignment
    # putting integration tests in shell scripts is cleaner
    # (1 line instead of 20ish lines)
    proc1 = subprocess.run(
        ["python3", "chat.py"],
        input="",
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc1.returncode == 0

    # Case 2: with message
    proc2 = subprocess.run(
        ["python3", "chat.py", "hello", "there"],
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc2.returncode in (0, 1)
    assert proc2.stdout or proc2.stderr
