"""Tests for argparse wiring and CLI input/output."""

import json

from cli.app import main
from cli.parser import build_parser
from models import Project, Task, User
from utils.store import load


def run(data_file, argv, capsys):
    """Run the CLI against a temp data file and return (code, stdout)."""
    code = main(argv, data_path=data_file)
    captured = capsys.readouterr()
    return code, captured.out


def test_help_without_args(data_file, capsys):
    code, out = run(data_file, [], capsys)
    assert code == 0
    assert "FOUNDRY" in out
    assert "add-user" in out


def test_add_user_and_list_users(data_file, capsys):
    code, out = run(
        data_file,
        ["add-user", "--name", "Alex", "--email", "alex@foundry.dev"],
        capsys,
    )
    assert code == 0
    assert "Alex" in out
    code, out = run(data_file, ["list-users", "--plain"], capsys)
    assert code == 0
    assert "Alex" in out
    assert "alex@foundry.dev" in out


def test_assignment_example_flow(data_file, capsys):
    assert run(data_file, ["add-user", "--name", "Alex"], capsys)[0] == 0
    assert (
        run(
            data_file,
            ["add-project", "--user", "Alex", "--title", "CLI Tool"],
            capsys,
        )[0]
        == 0
    )
    assert (
        run(
            data_file,
            [
                "add-task",
                "--project",
                "CLI Tool",
                "--title",
                "Implement add-task",
            ],
            capsys,
        )[0]
        == 0
    )
    code, out = run(
        data_file,
        ["complete-task", "--title", "Implement add-task"],
        capsys,
    )
    assert code == 0
    assert "Completed" in out
    load(data_file)
    assert Task.find_by_title("Implement add-task")[0].is_complete
    assert Project.find_by_title("CLI Tool").is_complete


def test_list_projects_for_user(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(data_file, ["add-user", "--name", "Maya"], capsys)
    run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    run(
        data_file,
        ["add-project", "--user", "Maya", "--title", "Portfolio Site"],
        capsys,
    )
    code, out = run(data_file, ["list-projects", "--user", "Alex", "--plain"], capsys)
    assert code == 0
    assert "CLI Tool" in out
    assert "Portfolio Site" not in out


def test_edit_project_persists(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    code, out = run(
        data_file,
        [
            "edit-project",
            "--title",
            "CLI Tool",
            "--description",
            "Ship the tracker",
            "--due",
            "2026-10-01",
        ],
        capsys,
    )
    assert code == 0
    payload = json.loads(data_file.read_text())
    assert payload["projects"][0]["description"] == "Ship the tracker"
    assert payload["projects"][0]["due_date"] == "2026-10-01"


def test_unknown_user_is_a_friendly_error(data_file, capsys):
    code, out = run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    assert code == 1
    assert "No user named 'Alex'" in out


def test_duplicate_user_error(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    code, out = run(data_file, ["add-user", "--name", "Alex"], capsys)
    assert code == 1
    assert "already exists" in out


def test_search_and_dashboard(data_file, capsys):
    run(data_file, ["seed"], capsys)
    code, out = run(data_file, ["search", "--query", "CLI"], capsys)
    assert code == 0
    assert "CLI Tool" in out
    code, out = run(data_file, ["dashboard"], capsys)
    assert code == 0
    assert "FOUNDRY" in out
    assert "Alex Rivera" in out or "CLI Tool" in out


def test_seed_refuses_to_overwrite(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    code, out = run(data_file, ["seed"], capsys)
    assert code == 1
    assert "already exists" in out
    code, _out = run(data_file, ["seed", "--force"], capsys)
    assert code == 0
    load(data_file)
    assert User.find_by_name("Alex Rivera") is not None


def test_complete_task_missing(data_file, capsys):
    code, out = run(
        data_file,
        ["complete-task", "--title", "Nope"],
        capsys,
    )
    assert code == 1
    assert "No task titled" in out


def test_parser_requires_name_for_add_user():
    parser = build_parser()
    args = parser.parse_args(["add-user", "--name", "Alex"])
    assert args.command == "add-user"
    assert args.name == "Alex"
    assert args.mutating is True


def test_parser_rejects_blank_name():
    parser = build_parser()
    try:
        parser.parse_args(["add-user", "--name", "   "])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("blank name should fail argparse validation")


def test_assign_and_contributor_commands(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(data_file, ["add-user", "--name", "Maya"], capsys)
    run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    run(
        data_file,
        ["add-task", "--project", "CLI Tool", "--title", "Implement add-task"],
        capsys,
    )
    assert (
        run(
            data_file,
            [
                "assign-task",
                "--title",
                "Implement add-task",
                "--user",
                "Alex",
            ],
            capsys,
        )[0]
        == 0
    )
    code, out = run(
        data_file,
        [
            "add-contributor",
            "--title",
            "Implement add-task",
            "--user",
            "Maya",
        ],
        capsys,
    )
    assert code == 0
    assert "Maya" in out
    code, out = run(
        data_file,
        ["list-tasks", "--project", "CLI Tool", "--plain"],
        capsys,
    )
    assert "Implement add-task" in out
    assert "Alex" in out


def test_malformed_data_file_from_cli(data_file, capsys):
    data_file.write_text("{bad", encoding="utf-8")
    code, out = run(data_file, ["list-users"], capsys)
    assert code == 1
    assert "not valid JSON" in out


def test_show_user_and_project(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    run(
        data_file,
        ["add-task", "--project", "CLI Tool", "--title", "Implement add-task"],
        capsys,
    )
    code, out = run(data_file, ["show-user", "--name", "Alex"], capsys)
    assert code == 0
    assert "Alex" in out
    code, out = run(data_file, ["show-project", "--title", "CLI Tool"], capsys)
    assert code == 0
    assert "Implement add-task" in out


def test_edit_and_remove_user(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    code, out = run(
        data_file,
        ["edit-user", "--name", "Alex", "--new-name", "Alex Rivera"],
        capsys,
    )
    assert code == 0
    assert "Alex Rivera" in out
    code, out = run(data_file, ["remove-user", "--name", "Alex Rivera"], capsys)
    assert code == 0
    assert "Removed Alex Rivera" in out


def test_start_reopen_edit_and_remove_task(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(
        data_file,
        ["add-project", "--user", "Alex", "--title", "CLI Tool"],
        capsys,
    )
    run(
        data_file,
        ["add-task", "--project", "CLI Tool", "--title", "Implement add-task"],
        capsys,
    )
    assert run(data_file, ["start-task", "--title", "Implement add-task"], capsys)[0] == 0
    assert (
        run(
            data_file,
            ["complete-task", "--title", "Implement add-task"],
            capsys,
        )[0]
        == 0
    )
    assert run(data_file, ["reopen-task", "--title", "Implement add-task"], capsys)[0] == 0
    code, out = run(
        data_file,
        [
            "edit-task",
            "--title",
            "Implement add-task",
            "--new-title",
            "Ship add-task",
            "--status",
            "in_progress",
        ],
        capsys,
    )
    assert code == 0
    assert "Ship add-task" in out
    code, out = run(data_file, ["remove-task", "--title", "Ship add-task"], capsys)
    assert code == 0
    assert "Removed task" in out


def test_collaborator_search_overdue_and_remove_project(data_file, capsys):
    run(data_file, ["add-user", "--name", "Alex"], capsys)
    run(data_file, ["add-user", "--name", "Maya"], capsys)
    run(
        data_file,
        [
            "add-project",
            "--user",
            "Alex",
            "--title",
            "CLI Tool",
            "--due",
            "2000-01-01",
        ],
        capsys,
    )
    run(
        data_file,
        ["add-task", "--project", "CLI Tool", "--title", "Implement add-task"],
        capsys,
    )
    code, out = run(
        data_file,
        ["add-collaborator", "--project", "CLI Tool", "--user", "Maya"],
        capsys,
    )
    assert code == 0
    assert "Maya" in out
    code, out = run(
        data_file,
        ["search-projects", "--query", "CLI", "--plain"],
        capsys,
    )
    assert code == 0
    assert "CLI Tool" in out
    code, out = run(data_file, ["overdue", "--plain"], capsys)
    assert code == 0
    assert "CLI Tool" in out
    code, out = run(data_file, ["remove-project", "--title", "CLI Tool"], capsys)
    assert code == 0
    assert "Removed 'CLI Tool'" in out
    code, out = run(data_file, ["overdue"], capsys)
    assert code == 0
    assert "Nothing is overdue" in out
