"""Tests for the project 4 tools: write_files, write_file, rm, run_doctests."""

import os
import git
import pytest

from tools.write_files import write_files
from tools.write_file import write_file
from tools.rm import rm
from tools.doctests import run_doctests


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo with user config for commit tests."""
    repo = git.Repo.init(str(tmp_path))
    with repo.config_writer() as cw:
        cw.set_value("user", "email", "test@docchat.test")
        cw.set_value("user", "name", "docchat test")
    return repo, tmp_path


def test_write_files_creates_file_and_commits(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    result = write_files([{"path": "hello.txt", "contents": "hello world"}], "add hello")
    assert "Wrote 1 file(s)" in result
    assert os.path.exists(tmp_path / "hello.txt")
    assert "hello world" == open(tmp_path / "hello.txt").read()


def test_write_files_no_changes(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    write_files([{"path": "hello.txt", "contents": "same content"}], "first")
    result = write_files([{"path": "hello.txt", "contents": "same content"}], "second")
    assert "no changes" in result


def test_write_files_creates_parent_dirs(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    result = write_files([{"path": "subdir/note.txt", "contents": "hi"}], "nested")
    assert "Wrote 1 file(s)" in result
    assert os.path.exists(tmp_path / "subdir" / "note.txt")


def test_write_file_non_python(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    result = write_file("readme.txt", "add readme", contents="hello")
    assert "Wrote 1 file(s)" in result
    assert "Doctest" not in result


def test_write_file_python_runs_doctests(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    content = 'def add(a, b):\n    """\n    >>> add(1, 2)\n    3\n    """\n    return a + b\n'
    result = write_file("math_tool.py", "add math_tool", contents=content)
    assert "Wrote 1 file(s)" in result
    assert "Doctest results" in result


def test_write_file_diff_patches_existing(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    write_files([{"path": "data.txt", "contents": "a\nb\nc\n"}], "init")
    diff = "@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n"
    result = write_file("data.txt", "patch data", diff=diff)
    assert "Wrote 1 file(s)" in result
    assert open(tmp_path / "data.txt").read() == "a\nB\nc\n"


def test_write_file_diff_wrong_line_numbers(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    write_files([{"path": "code.txt", "contents": "x\ny\nz\n"}], "init")
    diff = "@@ -99,3 +99,3 @@\n x\n-y\n+Y\n z\n"
    result = write_file("code.txt", "fuzzy patch", diff=diff)
    assert "Wrote 1 file(s)" in result
    assert open(tmp_path / "code.txt").read() == "x\nY\nz\n"


def test_write_file_missing_contents_and_diff(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    result = write_file("any.txt", "msg")
    assert "Error" in result


def test_rm_removes_file_and_commits(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    write_files([{"path": "bye.txt", "contents": "bye"}], "add bye")
    result = rm("bye.txt")
    assert "Removed 1 file(s)" in result
    assert not os.path.exists(tmp_path / "bye.txt")


def test_rm_glob_removes_multiple(git_repo, monkeypatch):
    repo, tmp_path = git_repo
    monkeypatch.chdir(tmp_path)

    write_files(
        [{"path": "a.log", "contents": "a"}, {"path": "b.log", "contents": "b"}],
        "add logs",
    )
    result = rm("*.log")
    assert "Removed 2 file(s)" in result


def test_run_doctests_on_real_file(monkeypatch):
    monkeypatch.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    result = run_doctests("tools/calculate.py")
    assert "passed" in result and "calculate" in result
