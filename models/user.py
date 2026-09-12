"""Users own projects and can be assigned to tasks as contributors."""

from models.person import Person
from utils.validators import clean_email, email_from_name


class User(Person):
    """A crew member who can own projects and work on tasks.

    Relationships:
    - one-to-many owner: User -> Project
    - many-to-many contributor: User <-> Task
    - many-to-many collaborator: User <-> Project
    """

    def __init__(self, name, email=None, entity_id=None, created_at=None):
        super().__init__(name, entity_id=entity_id, created_at=created_at)
        self.email = email or email_from_name(self.name)
        self._projects = []
        self._collaborations = []
        self._assigned_tasks = []
        self._contributed_tasks = []

    @classmethod
    def create(cls, name, email=None):
        """Build a User and register it in the class collection."""
        return cls(name, email)

    @classmethod
    def find_by_name(cls, name):
        """Return the user whose name matches, ignoring case."""
        if name is None:
            return None
        needle = str(name).strip().lower()
        for user in cls.all():
            if user.name.lower() == needle:
                return user
        return None

    @classmethod
    def find_by_email(cls, email):
        """Return the user with this email, or None."""
        if email is None:
            return None
        needle = str(email).strip().lower()
        for user in cls.all():
            if user.email == needle:
                return user
        return None

    @property
    def email(self):
        """Contact email. Unique across the crew."""
        return self._email

    @email.setter
    def email(self, value):
        self._email = clean_email(value)

    @property
    def projects(self):
        """Projects this user owns."""
        return list(self._projects)

    @property
    def collaborations(self):
        """Projects this user helps with but does not own."""
        return list(self._collaborations)

    @property
    def related_projects(self):
        """Owned projects plus collaborations, without duplicates."""
        seen = []
        for project in self._projects + self._collaborations:
            if project not in seen:
                seen.append(project)
        return seen

    @property
    def assigned_tasks(self):
        """Tasks where this user is the primary assignee."""
        return list(self._assigned_tasks)

    @property
    def contributed_tasks(self):
        """Tasks this user helps on as a contributor."""
        return list(self._contributed_tasks)

    def add_project(self, project):
        """Attach a project this user owns."""
        if project not in self._projects:
            self._projects.append(project)
        project._owner = self

    def remove_project(self, project):
        """Detach an owned project."""
        if project in self._projects:
            self._projects.remove(project)

    def add_collaboration(self, project):
        """Mark this user as a collaborator on a project."""
        if project not in self._collaborations:
            self._collaborations.append(project)

    def remove_collaboration(self, project):
        """Remove this user from a project's collaborator list."""
        if project in self._collaborations:
            self._collaborations.remove(project)

    def add_assigned_task(self, task):
        """Record a task assigned to this user."""
        if task not in self._assigned_tasks:
            self._assigned_tasks.append(task)

    def remove_assigned_task(self, task):
        """Drop a task from this user's assigned list."""
        if task in self._assigned_tasks:
            self._assigned_tasks.remove(task)

    def add_contributed_task(self, task):
        """Record a task this user contributes to."""
        if task not in self._contributed_tasks:
            self._contributed_tasks.append(task)

    def remove_contributed_task(self, task):
        """Drop a task from this user's contributor list."""
        if task in self._contributed_tasks:
            self._contributed_tasks.remove(task)

    def workload(self):
        """Count open tasks assigned to this user."""
        return sum(1 for task in self._assigned_tasks if not task.is_complete)

    def search_fields(self):
        """Search name, email, and owned project titles."""
        titles = [project.title for project in self._projects]
        return [self.name, self.email, *titles]

    def to_dict(self):
        """Serialize identity fields for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a User from a JSON record."""
        return cls(
            data["name"],
            data.get("email"),
            entity_id=data.get("id"),
            created_at=data.get("created_at"),
        )

    def __str__(self):
        return f"{self.name} <{self.email}>"

    def __repr__(self):
        return (
            f"User(id={self.id}, name={self.name!r}, email={self.email!r})"
        )
