"""Shared identity, timestamps, and in-memory registries for every model."""

from datetime import datetime, timezone


class SearchableMixin:
    """Lets a model answer whether it matches a free-text search query."""

    def search_fields(self):
        """Return the strings that should be searched. Subclasses override this."""
        return []

    def matches(self, query):
        """Return True when the query appears in any searchable field."""
        if query is None or not str(query).strip():
            return False
        needle = str(query).strip().lower()
        haystack = " ".join(str(field) for field in self.search_fields() if field)
        return needle in haystack.lower()


class Entity(SearchableMixin):
    """Base class with a per-subclass ID counter and an in-memory registry.

    Each subclass (Person, User, Project, Task) gets its own counter and list
    so IDs stay unique within that type.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._id_counter = 0
        cls._registry = []

    def __init__(self, entity_id=None, created_at=None):
        cls = type(self)
        if entity_id is None:
            cls._id_counter += 1
            entity_id = cls._id_counter
        else:
            entity_id = int(entity_id)
            if entity_id > cls._id_counter:
                cls._id_counter = entity_id
        self._id = entity_id
        self.created_at = created_at or _utc_now()
        if self not in cls._registry:
            cls._registry.append(self)

    @property
    def id(self):
        """Stable integer identity. IDs are assigned, not edited."""
        return self._id

    @classmethod
    def all(cls):
        """Return a copy of every instance currently in memory."""
        return list(cls._registry)

    @classmethod
    def find(cls, entity_id):
        """Return the instance with this id, or None if it is missing."""
        try:
            entity_id = int(entity_id)
        except (TypeError, ValueError):
            return None
        for item in cls._registry:
            if item.id == entity_id:
                return item
        return None

    @classmethod
    def clear_registry(cls):
        """Drop in-memory instances and reset the ID counter."""
        cls._registry.clear()
        cls._id_counter = 0

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    def __hash__(self):
        return hash((type(self).__name__, self.id))


def _utc_now():
    """Return a compact UTC timestamp for new records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
