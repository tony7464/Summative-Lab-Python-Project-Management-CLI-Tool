"""Field cleaners used by model property setters and the CLI."""

import re

from models.exceptions import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TASK_STATUSES = ("todo", "in_progress", "done")


def clean_name(value):
    """Strip extra spaces and require a 2-40 character display name."""
    if value is None or not str(value).strip():
        raise ValidationError("Name cannot be empty.")
    name = " ".join(str(value).split())
    if len(name) < 2:
        raise ValidationError("Name must be at least 2 characters.")
    if len(name) > 40:
        raise ValidationError("Name must be 40 characters or fewer.")
    return name


def clean_email(value):
    """Require a simple name@domain.tld email address."""
    if value is None or not str(value).strip():
        raise ValidationError("Email cannot be empty.")
    email = str(value).strip().lower()
    if not EMAIL_RE.match(email):
        raise ValidationError(f"'{value}' is not a valid email address.")
    return email


def clean_title(value, label="Title"):
    """Strip extra spaces and require a 2-80 character title."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{label} cannot be empty.")
    title = " ".join(str(value).split())
    if len(title) < 2:
        raise ValidationError(f"{label} must be at least 2 characters.")
    if len(title) > 80:
        raise ValidationError(f"{label} must be 80 characters or fewer.")
    return title


def clean_description(value):
    """Allow a blank description. Cap stored text at 240 characters."""
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > 240:
        raise ValidationError("Description must be 240 characters or fewer.")
    return text


def clean_status(value):
    """Normalize a task status to todo, in_progress, or done."""
    if value is None or not str(value).strip():
        raise ValidationError("Status cannot be empty.")
    status = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "complete": "done",
        "completed": "done",
        "finished": "done",
        "progress": "in_progress",
        "doing": "in_progress",
        "open": "todo",
        "pending": "todo",
    }
    status = aliases.get(status, status)
    if status not in TASK_STATUSES:
        raise ValidationError(
            f"Status must be one of: {', '.join(TASK_STATUSES)}."
        )
    return status


def email_from_name(name):
    """Build a local Foundry email when the caller does not pass one."""
    slug = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".")
    if not slug:
        raise ValidationError("Could not build an email from that name.")
    return f"{slug}@foundry.local"
