"""Dashboard, search, overdue, and seed command handlers."""

from models import Project, Task, User
from utils import display


def dashboard(args, workspace):
    """Print a studio-wide snapshot."""
    display.show_dashboard(User.all(), Project.all(), Task.all())


def overdue(args, workspace):
    """Print projects that are past due."""
    projects = workspace.overdue_projects()
    if not projects:
        display.info("Nothing is overdue.")
        return
    display.show_projects(projects, plain=args.plain)


def search(args, workspace):
    """Search users, projects, and tasks."""
    display.show_search(workspace.search(args.query))


def seed(args, workspace):
    """Load the demo Foundry crew."""
    workspace.seed(force=args.force)
    display.success("Loaded demo data. Run python main.py dashboard to look around.")
