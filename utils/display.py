"""Rich and tabulate helpers so command handlers stay focused on data."""

import sys

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate

from utils.dates import format_due_date

STATUS_STYLE = {
    "planning": "cyan",
    "todo": "yellow",
    "in_progress": "bright_blue",
    "overdue": "bold red",
    "complete": "green",
    "done": "green",
}


def get_console():
    """Build a console that writes to stdout so tests can capture it."""
    return Console(file=sys.stdout, highlight=False, soft_wrap=True)


def banner():
    """Print the Foundry welcome panel."""
    get_console().print(
        Panel.fit(
            "[bold bright_white]FOUNDRY[/bold bright_white]\n"
            "[dim]project tracker for a small crew[/dim]",
            border_style="bright_blue",
        )
    )


def success(message):
    """Print a successful action."""
    get_console().print(f"[bold green]✓[/bold green] {escape(str(message))}")


def error(message):
    """Print a failure the user can act on."""
    get_console().print(f"[bold red]✗[/bold red] {escape(str(message))}")


def warn(message):
    """Print a warning."""
    get_console().print(f"[yellow]![/yellow] {escape(str(message))}")


def info(message):
    """Print a neutral note."""
    get_console().print(escape(str(message)))


def empty(message):
    """Print an empty-state hint."""
    get_console().print(f"[dim]{escape(str(message))}[/dim]")


def _status_text(status):
    """Color a status label."""
    style = STATUS_STYLE.get(status, "white")
    return f"[{style}]{status}[/{style}]"


def _bar(progress):
    """Build a short ASCII progress bar from a 0-1 fraction."""
    filled = int(round(progress * 10))
    return "█" * filled + "░" * (10 - filled)


def render_table(headers, rows, plain=False):
    """Render a table with Rich, or tabulate when --plain is set."""
    if not rows:
        return
    if plain:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
        return
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    get_console().print(table)


def show_users(users, plain=False):
    """Print the crew roster."""
    if not users:
        empty("No users yet. Try: python main.py add-user --name Alex")
        return
    rows = []
    for user in users:
        rows.append(
            [
                str(user.id),
                user.name,
                user.email,
                str(len(user.related_projects)),
                str(user.workload()),
            ]
        )
    render_table(["ID", "Name", "Email", "Projects", "Open tasks"], rows, plain)


def show_projects(projects, plain=False):
    """Print a project table with progress and due dates."""
    if not projects:
        empty("No projects yet. Try: python main.py add-project --user Alex --title \"CLI Tool\"")
        return
    rows = []
    for project in projects:
        owner = project.owner.name if project.owner else "—"
        percent = f"{int(round(project.progress * 100))}%"
        if plain:
            status = project.status
            bar = percent
        else:
            status = _status_text(project.status)
            bar = f"{_bar(project.progress)} {percent}"
        rows.append(
            [
                str(project.id),
                project.title,
                owner,
                status,
                bar,
                format_due_date(project.due_date),
                str(len(project.tasks)),
            ]
        )
    render_table(
        ["ID", "Title", "Owner", "Status", "Progress", "Due", "Tasks"],
        rows,
        plain,
    )


def show_tasks(tasks, plain=False):
    """Print a task table."""
    if not tasks:
        empty("No tasks match that filter.")
        return
    rows = []
    for task in tasks:
        assignee = task.assigned_to.name if task.assigned_to else "—"
        project = task.project.title if task.project else "—"
        helpers = ", ".join(user.name for user in task.contributors) or "—"
        status = task.status if plain else _status_text(task.status)
        rows.append(
            [str(task.id), task.title, project, status, assignee, helpers]
        )
    render_table(
        ["ID", "Title", "Project", "Status", "Assigned", "Contributors"],
        rows,
        plain,
    )


def show_user_detail(user):
    """Print one user plus their projects and open work."""
    console = get_console()
    lines = [
        f"[bold]{user.name}[/bold]  <{user.email}>",
        f"Projects: {len(user.related_projects)}   Open tasks: {user.workload()}",
    ]
    console.print(Panel("\n".join(lines), title="User", border_style="cyan"))
    if user.related_projects:
        show_projects(user.related_projects)
    else:
        empty("This user has no projects yet.")


def show_project_detail(project):
    """Print one project, collaborators, and tasks."""
    console = get_console()
    owner = project.owner.name if project.owner else "unowned"
    helpers = ", ".join(user.name for user in project.collaborators) or "none"
    body = (
        f"[bold]{project.title}[/bold]\n"
        f"{project.description or 'No description.'}\n\n"
        f"Owner: {owner}\n"
        f"Collaborators: {helpers}\n"
        f"Status: {_status_text(project.status)}   "
        f"Progress: {_bar(project.progress)} "
        f"{int(round(project.progress * 100))}%\n"
        f"Due: {format_due_date(project.due_date)}"
    )
    console.print(Panel(body, title="Project", border_style="bright_blue"))
    show_tasks(project.tasks)


def show_dashboard(users, projects, tasks):
    """Print a studio snapshot: counts, projects, and overdue work."""
    banner()
    console = get_console()
    open_tasks = [task for task in tasks if not task.is_complete]
    overdue = [project for project in projects if project.is_overdue()]
    summary = (
        f"[bold]{len(users)}[/bold] users   "
        f"[bold]{len(projects)}[/bold] projects   "
        f"[bold]{len(open_tasks)}[/bold] open tasks   "
        f"[bold red]{len(overdue)}[/bold red] overdue"
    )
    console.print(Panel(summary, border_style="white"))
    if projects:
        console.print("\n[bold]Projects[/bold]")
        show_projects(projects)
    if overdue:
        console.print("\n[bold red]Overdue[/bold red]")
        show_projects(overdue)
    if open_tasks:
        console.print("\n[bold]Open tasks[/bold]")
        show_tasks(open_tasks)


def show_search(results):
    """Print grouped search hits."""
    users = results.get("users") or []
    projects = results.get("projects") or []
    tasks = results.get("tasks") or []
    if not users and not projects and not tasks:
        empty("No matches.")
        return
    console = get_console()
    if users:
        console.print("[bold]Users[/bold]")
        show_users(users)
    if projects:
        console.print("[bold]Projects[/bold]")
        show_projects(projects)
    if tasks:
        console.print("[bold]Tasks[/bold]")
        show_tasks(tasks)
