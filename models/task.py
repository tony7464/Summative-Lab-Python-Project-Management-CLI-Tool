"""A single unit of work that belongs to one project and many contributors."""

from models.entity import Entity
from utils.validators import clean_status, clean_title


class Task(Entity):
    """Work item owned by a Project.

    Relationships:
    - many tasks belong to one project (Project -> Task)
    - one optional assignee (Task -> User)
    - many-to-many contributors (Task <-> User)
    """

    STATUSES = ("todo", "in_progress", "done")

    def __init__(
        self,
        title,
        status="todo",
        assigned_to=None,
        entity_id=None,
        created_at=None,
    ):
        super().__init__(entity_id=entity_id, created_at=created_at)
        self.title = title
        self.status = status
        self._project = None
        self._assigned_to = None
        self._contributors = []
        if assigned_to is not None:
            self.assign_to(assigned_to)

    @classmethod
    def create(cls, title, status="todo", assigned_to=None):
        """Build a Task and register it in the class collection."""
        return cls(title, status=status, assigned_to=assigned_to)

    @classmethod
    def find_by_title(cls, title, project=None):
        """Return tasks whose title matches, optionally limited to one project."""
        if title is None:
            return []
        needle = str(title).strip().lower()
        matches = [
            task for task in cls.all() if task.title.lower() == needle
        ]
        if project is not None:
            matches = [task for task in matches if task.project == project]
        return matches

    @property
    def title(self):
        """Short label shown in the CLI."""
        return self._title

    @title.setter
    def title(self, value):
        self._title = clean_title(value, label="Task title")

    @property
    def status(self):
        """todo, in_progress, or done."""
        return self._status

    @status.setter
    def status(self, value):
        self._status = clean_status(value)

    @property
    def project(self):
        """Project this task belongs to."""
        return self._project

    @property
    def assigned_to(self):
        """Primary owner of the work, or None."""
        return self._assigned_to

    @property
    def contributors(self):
        """Users helping on this task. The assignee is not duplicated here."""
        return list(self._contributors)

    @property
    def is_complete(self):
        """True once the task has been marked done."""
        return self._status == "done"

    def assign_to(self, user):
        """Set or clear the primary assignee and keep both sides in sync."""
        if self._assigned_to is not None:
            self._assigned_to.remove_assigned_task(self)
        self._assigned_to = user
        if user is not None:
            user.add_assigned_task(self)

    def add_contributor(self, user):
        """Add a collaborator to this task. The assignee is skipped."""
        if user is None:
            return False
        if user == self._assigned_to:
            return False
        if user in self._contributors:
            return False
        self._contributors.append(user)
        user.add_contributed_task(self)
        return True

    def remove_contributor(self, user):
        """Remove a collaborator from this task."""
        if user in self._contributors:
            self._contributors.remove(user)
            user.remove_contributed_task(self)
            return True
        return False

    def start(self):
        """Move a todo task into in_progress. Returns True when the status changed."""
        if self._status == "done":
            return False
        if self._status == "in_progress":
            return False
        self.status = "in_progress"
        return True

    def complete(self):
        """Mark the task done. Returns True when the status changed."""
        if self._status == "done":
            return False
        self.status = "done"
        return True

    def reopen(self):
        """Send a done task back to todo. Returns True when the status changed."""
        if self._status != "done":
            return False
        self.status = "todo"
        return True

    def search_fields(self):
        """Search title, status, assignee, and parent project title."""
        return [
            self.title,
            self.status,
            self._assigned_to.name if self._assigned_to else "",
            self._project.title if self._project else "",
        ]

    def to_dict(self):
        """Serialize identity and relationship IDs for JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "project_id": self._project.id if self._project else None,
            "assigned_to_id": self._assigned_to.id if self._assigned_to else None,
            "contributor_ids": [user.id for user in self._contributors],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Task from a JSON record. Relationships are wired later."""
        return cls(
            data["title"],
            status=data.get("status", "todo"),
            entity_id=data.get("id"),
            created_at=data.get("created_at"),
        )

    def __str__(self):
        assignee = self._assigned_to.name if self._assigned_to else "unassigned"
        return f"[{self.status}] {self.title} → {assignee}"

    def __repr__(self):
        return (
            f"Task(id={self.id}, title={self.title!r}, status={self.status!r})"
        )
