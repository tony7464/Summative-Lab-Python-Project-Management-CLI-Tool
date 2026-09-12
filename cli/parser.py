"""argparse setup for every Foundry subcommand."""

import argparse

from cli import projects, reports, tasks, users


def non_empty(value):
    """argparse type: reject blank strings before a command runs."""
    if value is None or not str(value).strip():
        raise argparse.ArgumentTypeError("value cannot be empty")
    return str(value).strip()


def build_parser():
    """Return the top-level parser with user, project, task, and report commands."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Foundry — a command-line project tracker for a small crew.",
        epilog=(
            "examples:\n"
            "  python main.py add-user --name Alex\n"
            "  python main.py add-project --user Alex --title \"CLI Tool\"\n"
            "  python main.py add-task --project \"CLI Tool\" --title \"Implement add-task\"\n"
            "  python main.py complete-task --title \"Implement add-task\"\n"
            "  python main.py list-projects --user Alex\n"
            "  python main.py dashboard\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data",
        dest="data_path",
        help="Path to the JSON data file (default: data/tracker.json)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Write debug logs to data/tracker.log",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="command",
        help="Available commands",
    )

    _add_user_commands(subparsers)
    _add_project_commands(subparsers)
    _add_task_commands(subparsers)
    _add_report_commands(subparsers)
    return parser


def _plain_flag(parser):
    """Add the --plain flag that switches Rich tables to tabulate."""
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Print a simple table (tabulate) instead of Rich formatting",
    )


def _add_user_commands(subparsers):
    """Register user subcommands."""
    add = subparsers.add_parser("add-user", help="Create a user")
    add.add_argument("--name", "-n", required=True, type=non_empty, help="Display name")
    add.add_argument("--email", "-e", type=non_empty, help="Email (optional)")
    add.set_defaults(func=users.add_user, mutating=True)

    listed = subparsers.add_parser("list-users", help="List every user")
    _plain_flag(listed)
    listed.set_defaults(func=users.list_users, mutating=False)

    show = subparsers.add_parser("show-user", help="Show one user and their projects")
    show.add_argument("--name", "-n", required=True, type=non_empty)
    show.set_defaults(func=users.show_user, mutating=False)

    edit = subparsers.add_parser("edit-user", help="Rename a user or change their email")
    edit.add_argument("--name", "-n", required=True, type=non_empty, help="Current name")
    edit.add_argument("--new-name", type=non_empty, help="New display name")
    edit.add_argument("--email", "-e", type=non_empty)
    edit.set_defaults(func=users.edit_user, mutating=True)

    remove = subparsers.add_parser("remove-user", help="Delete a user and their projects")
    remove.add_argument("--name", "-n", required=True, type=non_empty)
    remove.set_defaults(func=users.remove_user, mutating=True)


def _add_project_commands(subparsers):
    """Register project subcommands."""
    add = subparsers.add_parser("add-project", help="Add a project for a user")
    add.add_argument("--user", "-u", required=True, type=non_empty, help="Owner name")
    add.add_argument("--title", "-t", required=True, type=non_empty)
    add.add_argument("--description", "-d", default="", help="Short summary")
    add.add_argument("--due", help="Due date, e.g. 2026-10-01")
    add.set_defaults(func=projects.add_project, mutating=True)

    listed = subparsers.add_parser("list-projects", help="List projects, optionally by user")
    listed.add_argument("--user", "-u", type=non_empty, help="Only this user's projects")
    _plain_flag(listed)
    listed.set_defaults(func=projects.list_projects, mutating=False)

    show = subparsers.add_parser("show-project", help="Show one project and its tasks")
    show.add_argument("--title", "-t", required=True, type=non_empty)
    show.set_defaults(func=projects.show_project, mutating=False)

    edit = subparsers.add_parser("edit-project", help="Edit a project's details")
    edit.add_argument("--title", "-t", required=True, type=non_empty, help="Current title")
    edit.add_argument("--new-title", type=non_empty)
    edit.add_argument("--description", "-d")
    edit.add_argument("--due")
    edit.set_defaults(func=projects.edit_project, mutating=True)

    remove = subparsers.add_parser("remove-project", help="Delete a project and its tasks")
    remove.add_argument("--title", "-t", required=True, type=non_empty)
    remove.set_defaults(func=projects.remove_project, mutating=True)

    search = subparsers.add_parser("search-projects", help="Search projects by text or user")
    search.add_argument("--query", "-q", type=non_empty, help="Text to match")
    search.add_argument("--user", "-u", type=non_empty)
    _plain_flag(search)
    search.set_defaults(func=projects.search_projects, mutating=False)

    collab = subparsers.add_parser("add-collaborator", help="Add a user to a project")
    collab.add_argument("--project", "-p", required=True, type=non_empty)
    collab.add_argument("--user", "-u", required=True, type=non_empty)
    collab.set_defaults(func=projects.add_collaborator, mutating=True)


def _add_task_commands(subparsers):
    """Register task subcommands."""
    add = subparsers.add_parser("add-task", help="Add a task to a project")
    add.add_argument("--project", "-p", required=True, type=non_empty)
    add.add_argument("--title", "-t", required=True, type=non_empty)
    add.add_argument("--assign", "-a", type=non_empty, help="Assignee name")
    add.add_argument("--status", choices=["todo", "in_progress", "done"])
    add.set_defaults(func=tasks.add_task, mutating=True)

    listed = subparsers.add_parser("list-tasks", help="List tasks")
    listed.add_argument("--project", "-p", type=non_empty)
    listed.add_argument("--user", "-u", type=non_empty)
    listed.add_argument("--status", choices=["todo", "in_progress", "done"])
    _plain_flag(listed)
    listed.set_defaults(func=tasks.list_tasks, mutating=False)

    complete = subparsers.add_parser("complete-task", help="Mark a task complete")
    complete.add_argument("--title", "-t", required=True, type=non_empty)
    complete.add_argument("--project", "-p", type=non_empty, help="Needed if titles collide")
    complete.set_defaults(func=tasks.complete_task, mutating=True)

    start = subparsers.add_parser("start-task", help="Move a task to in progress")
    start.add_argument("--title", "-t", required=True, type=non_empty)
    start.add_argument("--project", "-p", type=non_empty)
    start.set_defaults(func=tasks.start_task, mutating=True)

    reopen = subparsers.add_parser("reopen-task", help="Send a completed task back to todo")
    reopen.add_argument("--title", "-t", required=True, type=non_empty)
    reopen.add_argument("--project", "-p", type=non_empty)
    reopen.set_defaults(func=tasks.reopen_task, mutating=True)

    assign = subparsers.add_parser("assign-task", help="Assign a task to a user")
    assign.add_argument("--title", "-t", required=True, type=non_empty)
    assign.add_argument("--user", "-u", required=True, type=non_empty)
    assign.add_argument("--project", "-p", type=non_empty)
    assign.set_defaults(func=tasks.assign_task, mutating=True)

    contributor = subparsers.add_parser(
        "add-contributor",
        help="Add a contributor to a task",
    )
    contributor.add_argument("--title", "-t", required=True, type=non_empty, help="Task title")
    contributor.add_argument("--user", "-u", required=True, type=non_empty)
    contributor.add_argument("--project", "-p", type=non_empty)
    contributor.set_defaults(func=tasks.add_contributor, mutating=True)

    edit = subparsers.add_parser("edit-task", help="Rename a task or change its status")
    edit.add_argument("--title", "-t", required=True, type=non_empty, help="Current title")
    edit.add_argument("--project", "-p", type=non_empty)
    edit.add_argument("--new-title", type=non_empty)
    edit.add_argument("--status", choices=["todo", "in_progress", "done"])
    edit.set_defaults(func=tasks.edit_task, mutating=True)

    remove = subparsers.add_parser("remove-task", help="Delete a task")
    remove.add_argument("--title", "-t", required=True, type=non_empty)
    remove.add_argument("--project", "-p", type=non_empty)
    remove.set_defaults(func=tasks.remove_task, mutating=True)


def _add_report_commands(subparsers):
    """Register dashboard, search, overdue, and seed commands."""
    dash = subparsers.add_parser("dashboard", help="Show a studio-wide snapshot")
    dash.set_defaults(func=reports.dashboard, mutating=False)

    late = subparsers.add_parser("overdue", help="List projects that are past due")
    _plain_flag(late)
    late.set_defaults(func=reports.overdue, mutating=False)

    search = subparsers.add_parser("search", help="Search users, projects, and tasks")
    search.add_argument("--query", "-q", required=True, type=non_empty)
    search.set_defaults(func=reports.search, mutating=False)

    seed = subparsers.add_parser("seed", help="Load demo users, projects, and tasks")
    seed.add_argument(
        "--force",
        action="store_true",
        help="Replace any data that is already stored",
    )
    seed.set_defaults(func=reports.seed, mutating=True)
