"""Domain errors used by the models, validators, and persistence layer."""


class TrackerError(Exception):
    """Base error for anything the CLI should print as a friendly failure."""


class ValidationError(TrackerError):
    """A field value did not pass validation."""


class NotFoundError(TrackerError):
    """The requested user, project, or task does not exist."""


class DuplicateError(TrackerError):
    """An entity with this unique name or title already exists."""


class StorageError(TrackerError):
    """The JSON data file could not be read or written."""
