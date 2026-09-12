"""Person is the inherited base for anyone the tracker knows by name."""

from models.entity import Entity
from utils.validators import clean_name


class Person(Entity):
    """A named human. User adds email, projects, and assigned work."""

    def __init__(self, name, entity_id=None, created_at=None):
        super().__init__(entity_id=entity_id, created_at=created_at)
        self.name = name

    @property
    def name(self):
        """Display name used by CLI lookups."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = clean_name(value)

    def search_fields(self):
        """Include the person's name in free-text search."""
        return [self.name]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{type(self).__name__}(id={self.id}, name={self.name!r})"
