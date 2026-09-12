"""In-memory graph of users, projects, and tasks plus the operations on it."""

from datetime import date, timedelta

from models.exceptions import DuplicateError, NotFoundError, ValidationError
from models.project import Project
from models.task import Task
from models.user import User


class Workspace:
    """Service layer that owns relationships and lookup rules.

    The CLI talks to a Workspace. Persistence loads and saves snapshots of it.
    """

    def add_user(self, name, email=None):
        """Create a user. Names and emails must be unique."""
        from utils.validators import email_from_name

        if User.find_by_name(name):
            raise DuplicateError(f"A user named '{name}' already exists.")
        resolved = email or email_from_name(name)
        if User.find_by_email(resolved):
            raise DuplicateError(f"A user with email '{resolved}' already exists.")
        return User.create(name, resolved)

    def edit_user(self, name, new_name=None, email=None):
        """Rename a user or change their email."""
        user = self.get_user(name)
        if new_name and new_name.strip().lower() != user.name.lower():
            existing = User.find_by_name(new_name)
            if existing and existing is not user:
                raise DuplicateError(f"A user named '{new_name}' already exists.")
            user.name = new_name
        if email and email.strip().lower() != user.email:
            existing = User.find_by_email(email)
            if existing and existing is not user:
                raise DuplicateError(f"A user with email '{email}' already exists.")
            user.email = email
        return user

    def remove_user(self, name):
        """Delete a user and cascade their owned projects and tasks."""
        user = self.get_user(name)
        removed_projects = list(user.projects)
        removed_tasks = []
        for project in removed_projects:
            removed_tasks.extend(self._delete_project(project))
        for project in list(user.collaborations):
            project.remove_collaborator(user)
        for task in list(user.assigned_tasks):
            task.assign_to(None)
        for task in list(user.contributed_tasks):
            task.remove_contributor(user)
        User._registry.remove(user)
        return user, removed_projects, removed_tasks

    def get_user(self, name):
        """Return a user or raise NotFoundError."""
        user = User.find_by_name(name)
        if user is None:
            raise NotFoundError(f"No user named '{name}'.")
        return user

    def add_project(self, user_name, title, description="", due_date=None):
        """Create a project owned by the named user."""
        owner = self.get_user(user_name)
        if Project.find_by_title(title):
            raise DuplicateError(f"A project titled '{title}' already exists.")
        return Project.create(title, description, due_date, owner=owner)

    def edit_project(self, title, new_title=None, description=None, due_date=None):
        """Update a project's title, description, or due date."""
        project = self.get_project(title)
        if new_title and new_title.strip().lower() != project.title.lower():
            existing = Project.find_by_title(new_title)
            if existing and existing is not project:
                raise DuplicateError(f"A project titled '{new_title}' already exists.")
            project.title = new_title
        if description is not None:
            project.description = description
        if due_date is not None:
            project.due_date = due_date
        return project

    def remove_project(self, title):
        """Delete a project and every task on it."""
        project = self.get_project(title)
        tasks = self._delete_project(project)
        return project, tasks

    def get_project(self, title):
        """Return a project or raise NotFoundError."""
        project = Project.find_by_title(title)
        if project is None:
            raise NotFoundError(f"No project titled '{title}'.")
        return project

    def projects_for(self, user_name):
        """Return owned projects and collaborations for a user."""
        return self.get_user(user_name).related_projects

    def search_projects(self, query=None, user_name=None):
        """Filter projects by free text and/or owner name."""
        projects = Project.all()
        if user_name:
            allowed = set(self.projects_for(user_name))
            projects = [project for project in projects if project in allowed]
        if query:
            projects = [project for project in projects if project.matches(query)]
        return projects

    def add_collaborator(self, project_title, user_name):
        """Add a user as a collaborator on a project they do not own."""
        project = self.get_project(project_title)
        user = self.get_user(user_name)
        if user == project.owner:
            raise ValidationError(
                f"{user.name} already owns '{project.title}'."
            )
        if not project.add_collaborator(user):
            raise DuplicateError(
                f"{user.name} is already a collaborator on '{project.title}'."
            )
        return project, user

    def add_task(self, project_title, title, assign=None, status="todo"):
        """Create a task on a project and optionally assign it."""
        project = self.get_project(project_title)
        if Task.find_by_title(title, project=project):
            raise DuplicateError(
                f"'{project.title}' already has a task titled '{title}'."
            )
        assignee = self.get_user(assign) if assign else None
        task = Task.create(title, status=status, assigned_to=assignee)
        project.add_task(task)
        return task

    def edit_task(self, title, project_title=None, new_title=None, status=None):
        """Rename a task or change its status."""
        task = self.get_task(title, project_title)
        if new_title and new_title.strip().lower() != task.title.lower():
            if Task.find_by_title(new_title, project=task.project):
                raise DuplicateError(
                    f"'{task.project.title}' already has a task titled '{new_title}'."
                )
            task.title = new_title
        if status is not None:
            task.status = status
        return task

    def complete_task(self, title, project_title=None):
        """Mark a task done. Raises if it is already complete."""
        task = self.get_task(title, project_title)
        if not task.complete():
            raise ValidationError(f"Task '{task.title}' is already complete.")
        return task

    def start_task(self, title, project_title=None):
        """Move a task to in_progress."""
        task = self.get_task(title, project_title)
        if task.is_complete:
            raise ValidationError(
                f"Task '{task.title}' is already complete. Reopen it first."
            )
        if not task.start():
            raise ValidationError(f"Task '{task.title}' is already in progress.")
        return task

    def reopen_task(self, title, project_title=None):
        """Send a completed task back to todo."""
        task = self.get_task(title, project_title)
        if not task.reopen():
            raise ValidationError(f"Task '{task.title}' is not complete.")
        return task

    def assign_task(self, title, user_name, project_title=None):
        """Set the primary assignee on a task."""
        task = self.get_task(title, project_title)
        user = self.get_user(user_name)
        task.remove_contributor(user)
        task.assign_to(user)
        return task

    def add_contributor(self, title, user_name, project_title=None):
        """Add a contributor to a task (many-to-many)."""
        task = self.get_task(title, project_title)
        user = self.get_user(user_name)
        if not task.add_contributor(user):
            if user == task.assigned_to:
                raise ValidationError(
                    f"{user.name} is already assigned to '{task.title}'."
                )
            raise DuplicateError(
                f"{user.name} is already a contributor on '{task.title}'."
            )
        return task, user

    def remove_task(self, title, project_title=None):
        """Delete a task and detach people from it."""
        task = self.get_task(title, project_title)
        self._detach_task(task)
        Task._registry.remove(task)
        return task

    def get_task(self, title, project_title=None):
        """Resolve a task by title, using project when the title is shared."""
        project = self.get_project(project_title) if project_title else None
        matches = Task.find_by_title(title, project=project)
        if not matches:
            where = f" on '{project_title}'" if project_title else ""
            raise NotFoundError(f"No task titled '{title}'{where}.")
        if len(matches) > 1:
            titles = ", ".join(
                sorted({task.project.title for task in matches if task.project})
            )
            raise ValidationError(
                f"More than one task is titled '{title}' "
                f"(projects: {titles}). Pass --project to pick one."
            )
        return matches[0]

    def list_tasks(self, project_title=None, user_name=None, status=None):
        """Return tasks filtered by project, assignee, and/or status."""
        tasks = Task.all()
        if project_title:
            project = self.get_project(project_title)
            tasks = [task for task in tasks if task.project == project]
        if user_name:
            user = self.get_user(user_name)
            tasks = [
                task
                for task in tasks
                if task.assigned_to == user or user in task.contributors
            ]
        if status:
            wanted = status.strip().lower()
            tasks = [task for task in tasks if task.status == wanted]
        return tasks

    def search(self, query):
        """Search users, projects, and tasks for a query string."""
        if query is None or not str(query).strip():
            raise ValidationError("Search query cannot be empty.")
        return {
            "users": [user for user in User.all() if user.matches(query)],
            "projects": [project for project in Project.all() if project.matches(query)],
            "tasks": [task for task in Task.all() if task.matches(query)],
        }

    def overdue_projects(self):
        """Return projects that are past due and still open."""
        return Project.overdue_projects()

    def seed(self, force=False):
        """Load a small demo crew so the dashboard has something to show."""
        if User.all() and not force:
            raise ValidationError(
                "Data already exists. Re-run with --force to replace it."
            )
        if force:
            reset_all()
        yesterday = date.today() - timedelta(days=1)
        soon = date.today() + timedelta(days=14)
        later = date.today() + timedelta(days=30)

        alex = self.add_user("Alex Rivera", "alex@foundry.dev")
        maya = self.add_user("Maya Chen", "maya@foundry.dev")
        sam = self.add_user("Sam Ortiz", "sam@foundry.dev")

        cli = self.add_project(
            "Alex Rivera",
            "CLI Tool",
            "Command-line project tracker for the Foundry crew.",
            soon,
        )
        portfolio = self.add_project(
            "Maya Chen",
            "Portfolio Site",
            "Personal site for Maya's freelance work.",
            yesterday,
        )
        billing = self.add_project(
            "Sam Ortiz",
            "Billing API",
            "Invoices and payment webhooks for studio clients.",
            later,
        )

        self.add_collaborator("CLI Tool", "Maya Chen")

        add_task = self.add_task("CLI Tool", "Implement add-task", assign="Alex Rivera")
        add_task.status = "in_progress"
        persist = self.add_task("CLI Tool", "Wire up JSON persistence", assign="Maya Chen")
        persist.complete()
        tests = self.add_task("CLI Tool", "Write pytest coverage", assign="Alex Rivera")
        tests.add_contributor(sam)

        self.add_task("Portfolio Site", "Design project grid", assign="Maya Chen").complete()
        self.add_task("Portfolio Site", "Ship case study copy", assign="Maya Chen")

        self.add_task("Billing API", "Sketch invoice schema", assign="Sam Ortiz")
        self.add_task("Billing API", "Add webhook retries", assign="Sam Ortiz")

        return {
            "users": [alex, maya, sam],
            "projects": [cli, portfolio, billing],
            "tasks": Task.all(),
        }

    def _delete_project(self, project):
        """Remove a project, its tasks, and collaborator links."""
        tasks = list(project.tasks)
        for task in tasks:
            self._detach_task(task)
            Task._registry.remove(task)
        for user in list(project.collaborators):
            project.remove_collaborator(user)
        if project.owner:
            project.owner.remove_project(project)
        if project in Project._registry:
            Project._registry.remove(project)
        return tasks

    def _detach_task(self, task):
        """Clear assignee, contributors, and project links for a task."""
        task.assign_to(None)
        for user in list(task.contributors):
            task.remove_contributor(user)
        if task.project:
            task.project.remove_task(task)


def reset_all():
    """Clear every in-memory registry. Used on reload and in tests."""
    User.clear_registry()
    Project.clear_registry()
    Task.clear_registry()
