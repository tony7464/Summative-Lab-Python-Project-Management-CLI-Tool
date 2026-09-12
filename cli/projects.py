"""Project command handlers."""

from models import Project
from utils import display


def add_project(args, workspace):
    """Create a project owned by --user."""
    project = workspace.add_project(
        args.user,
        args.title,
        description=args.description or "",
        due_date=args.due,
    )
    display.success(f"Added project {project}")


def list_projects(args, workspace):
    """List all projects, or only those tied to --user."""
    if args.user:
        projects = workspace.projects_for(args.user)
    else:
        projects = Project.all()
    display.show_projects(projects, plain=args.plain)


def show_project(args, workspace):
    """Print one project and its tasks."""
    display.show_project_detail(workspace.get_project(args.title))


def edit_project(args, workspace):
    """Update title, description, or due date."""
    project = workspace.edit_project(
        args.title,
        new_title=args.new_title,
        description=args.description,
        due_date=args.due,
    )
    display.success(f"Updated project {project}")


def remove_project(args, workspace):
    """Delete a project and its tasks."""
    project, tasks = workspace.remove_project(args.title)
    display.success(f"Removed '{project.title}' and {len(tasks)} task(s).")


def search_projects(args, workspace):
    """Filter projects by query and/or user."""
    projects = workspace.search_projects(query=args.query, user_name=args.user)
    display.show_projects(projects, plain=args.plain)


def add_collaborator(args, workspace):
    """Let another user join a project."""
    project, user = workspace.add_collaborator(args.project, args.user)
    display.success(f"Added {user.name} as a collaborator on '{project.title}'.")
