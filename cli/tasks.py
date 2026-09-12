"""Task command handlers."""

from utils import display


def add_task(args, workspace):
    """Create a task on --project."""
    task = workspace.add_task(
        args.project,
        args.title,
        assign=args.assign,
        status=args.status or "todo",
    )
    display.success(f"Added task {task}")


def list_tasks(args, workspace):
    """List tasks filtered by project, user, or status."""
    tasks = workspace.list_tasks(
        project_title=args.project,
        user_name=args.user,
        status=args.status,
    )
    display.show_tasks(tasks, plain=args.plain)


def complete_task(args, workspace):
    """Mark a task done."""
    task = workspace.complete_task(args.title, args.project)
    extra = ""
    if task.project and task.project.is_complete:
        extra = f" '{task.project.title}' is now complete."
    display.success(f"Completed '{task.title}'.{extra}")


def start_task(args, workspace):
    """Move a task to in_progress."""
    task = workspace.start_task(args.title, args.project)
    display.success(f"Started '{task.title}'.")


def reopen_task(args, workspace):
    """Send a completed task back to todo."""
    task = workspace.reopen_task(args.title, args.project)
    display.success(f"Reopened '{task.title}'.")


def assign_task(args, workspace):
    """Set the primary assignee."""
    task = workspace.assign_task(args.title, args.user, args.project)
    display.success(f"Assigned '{task.title}' to {task.assigned_to.name}.")


def add_contributor(args, workspace):
    """Add a contributor to a task."""
    task, user = workspace.add_contributor(args.title, args.user, args.project)
    display.success(f"Added {user.name} as a contributor on '{task.title}'.")


def edit_task(args, workspace):
    """Rename a task or change its status."""
    task = workspace.edit_task(
        args.title,
        project_title=args.project,
        new_title=args.new_title,
        status=args.status,
    )
    display.success(f"Updated task {task}")


def remove_task(args, workspace):
    """Delete a task."""
    task = workspace.remove_task(args.title, args.project)
    display.success(f"Removed task '{task.title}'.")
