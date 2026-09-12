"""User command handlers."""

from utils import display


def add_user(args, workspace):
    """Create a user from --name and optional --email."""
    user = workspace.add_user(args.name, args.email)
    display.success(f"Added user {user}")


def list_users(args, workspace):
    """Print every user in the crew."""
    display.show_users(workspace_users(), plain=args.plain)


def show_user(args, workspace):
    """Print one user and their projects."""
    display.show_user_detail(workspace.get_user(args.name))


def edit_user(args, workspace):
    """Rename a user or change their email."""
    user = workspace.edit_user(args.name, new_name=args.new_name, email=args.email)
    display.success(f"Updated user {user}")


def remove_user(args, workspace):
    """Delete a user and the projects they own."""
    user, projects, tasks = workspace.remove_user(args.name)
    display.success(
        f"Removed {user.name} along with {len(projects)} project(s) "
        f"and {len(tasks)} task(s)."
    )


def workspace_users():
    """Return the current user collection for list commands."""
    from models import User

    return User.all()
