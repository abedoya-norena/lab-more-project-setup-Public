import types

from chat import Chat
from tools.compact import compact


def test_provider_models(monkeypatch):
    fake_openai_module = types.SimpleNamespace(OpenAI=lambda **kwargs: object())
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai_module)

    assert "openai" in Chat(provider="openai").MODEL
    assert "anthropic" in Chat(provider="anthropic").MODEL
    assert "google" in Chat(provider="google").MODEL
    assert Chat(provider="groq").provider == "groq"


class DummyMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content


class _FakeChat:
    def __init__(self, *args, **kwargs):
        self.MODEL = "fake-model"
        self.messages = []
        completion = types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content="summary output")
                )
            ]
        )
        self.client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(create=lambda **kwargs: completion)
            )
        )


def test_compact_function_runs(monkeypatch):
    monkeypatch.setattr("chat.Chat", _FakeChat)
    messages = [
        {"role": "user", "content": "hello"},
        DummyMessage("assistant", "hi"),
    ]
    summary = compact(messages)
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_compact_replaces_messages(monkeypatch):
    monkeypatch.setattr("chat.Chat", _FakeChat)
    chat = Chat()
    chat.messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]

    summary = compact(chat.messages)
    chat.messages = [{"role": "system", "content": summary}]
    
    assert len(chat.messages) == 1