"""A project owned by one user and broken into many tasks."""

from datetime import date

from models.entity import Entity
from utils.dates import format_due_date, parse_due_date
from utils.validators import clean_description, clean_title


class Project(Entity):
    """Workstream owned by a User.

    Relationships:
    - many projects belong to one owner (User -> Project)
    - many tasks belong to one project (Project -> Task)
    - many collaborators can join a project they do not own
    """

    def __init__(
        self,
        title,
        description="",
        due_date=None,
        owner=None,
        entity_id=None,
        created_at=None,
    ):
        super().__init__(entity_id=entity_id, created_at=created_at)
        self.title = title
        self.description = description
        self.due_date = due_date
        self._owner = None
        self._tasks = []
        self._collaborators = []
        if owner is not None:
            owner.add_project(self)

    @classmethod
    def create(cls, title, description="", due_date=None, owner=None):
        """Build a Project and register it in the class collection."""
        return cls(title, description, due_date, owner)

    @classmethod
    def find_by_title(cls, title):
        """Return the project whose title matches, ignoring case."""
        if title is None:
            return None
        needle = str(title).strip().lower()
        for project in cls.all():
            if project.title.lower() == needle:
                return project
        return None

    @classmethod
    def overdue_projects(cls, today=None):
        """Return every project that is past due and not complete."""
        return [project for project in cls.all() if project.is_overdue(today)]

    @property
    def title(self):
        """Unique title used by CLI lookups."""
        return self._title

    @title.setter
    def title(self, value):
        self._title = clean_title(value, label="Project title")

    @property
    def description(self):
        """Optional short summary of the work."""
        return self._description

    @description.setter
    def description(self, value):
        self._description = clean_description(value)

    @property
    def due_date(self):
        """Optional due date as a datetime.date."""
        return self._due_date

    @due_date.setter
    def due_date(self, value):
        self._due_date = parse_due_date(value) if value not in (None, "") else None

    @property
    def owner(self):
        """User who owns this project."""
        return self._owner

    @property
    def tasks(self):
        """Tasks that belong to this project."""
        return list(self._tasks)

    @property
    def collaborators(self):
        """Users helping on the project who are not the owner."""
        return list(self._collaborators)

    @property
    def is_complete(self):
        """True when the project has tasks and every task is done."""
        return bool(self._tasks) and all(task.is_complete for task in self._tasks)

    def is_overdue(self, today=None):
        """True when the due date is in the past and work is still open."""
        if self._due_date is None or self.is_complete:
            return False
        return self._due_date < (today or date.today())

    @property
    def progress(self):
        """Fraction of tasks that are done, from 0.0 to 1.0."""
        if not self._tasks:
            return 0.0
        done = sum(1 for task in self._tasks if task.is_complete)
        return done / len(self._tasks)

    @property
    def status(self):
        """Derived label: planning, in_progress, overdue, or complete."""
        if self.is_complete:
            return "complete"
        if self.is_overdue():
            return "overdue"
        if any(task.status != "todo" for task in self._tasks):
            return "in_progress"
        return "planning"

    def add_task(self, task):
        """Attach a task and point it back at this project."""
        if task not in self._tasks:
            self._tasks.append(task)
        task._project = self

    def remove_task(self, task):
        """Detach a task from this project."""
        if task in self._tasks:
            self._tasks.remove(task)
        task._project = None

    def add_collaborator(self, user):
        """Let another user join the project. Owner is rejected."""
        if user is None or user == self._owner:
            return False
        if user in self._collaborators:
            return False
        self._collaborators.append(user)
        user.add_collaboration(self)
        return True

    def remove_collaborator(self, user):
        """Remove a collaborator from the project."""
        if user in self._collaborators:
            self._collaborators.remove(user)
            user.remove_collaboration(self)
            return True
        return False

    def search_fields(self):
        """Search title, description, owner, and task titles."""
        task_titles = [task.title for task in self._tasks]
        owner_name = self._owner.name if self._owner else ""
        return [self.title, self.description, owner_name, *task_titles]

    def to_dict(self):
        """Serialize identity and relationship IDs for JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": format_due_date(self._due_date) if self._due_date else None,
            "owner_id": self._owner.id if self._owner else None,
            "collaborator_ids": [user.id for user in self._collaborators],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Project from a JSON record. Relationships are wired later."""
        due = data.get("due_date")
        return cls(
            data["title"],
            description=data.get("description", ""),
            due_date=None if due in (None, "—", "") else due,
            entity_id=data.get("id"),
            created_at=data.get("created_at"),
        )

    def __str__(self):
        owner = self._owner.name if self._owner else "unowned"
        due = format_due_date(self._due_date)
        percent = int(round(self.progress * 100))
        return f"{self.title} ({owner}) [{self.status} {percent}% due {due}]"

    def __repr__(self):
        return f"Project(id={self.id}, title={self.title!r})"
