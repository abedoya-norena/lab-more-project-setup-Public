import sys
import subprocess
import os


def run_chat(input_text):
    env = os.environ.copy()
    env["GROQ_API_KEY"] = "test"
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.run(
        [sys.executable, "chat.py"],
        input=input_text,
        text=True,
        capture_output=True,
        env=env,
    )
    return proc.stdout


def test_all_repl_commands():
    out = run_chat(
        "/help\n"
        "/ls .\n"
        "/cat chat.py\n"
        "/grep Chat chat.py\n"
        "/calculate 2+2\n"
        "/compact\n"
        "/unknown\n"
    )

    assert "Available commands" in out
    assert "class Chat" in out
    assert "Chat" in out
    assert "4" in out
