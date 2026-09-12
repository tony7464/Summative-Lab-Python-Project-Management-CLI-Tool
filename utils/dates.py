"""Due-date parsing and formatting built on python-dateutil."""

from datetime import date, datetime

from dateutil import parser as date_parser

from models.exceptions import ValidationError


def parse_due_date(value):
    """Turn a user-supplied date into a datetime.date.

    Accepts ISO dates (2026-10-01) and common written forms (Oct 1 2026).
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        parsed = date_parser.parse(str(value).strip(), fuzzy=False)
    except (ValueError, OverflowError, TypeError) as exc:
        raise ValidationError(
            f"Could not read due date '{value}'. Try YYYY-MM-DD."
        ) from exc
    return parsed.date()


def format_due_date(value):
    """Return an ISO date string, or a dash when no due date is set."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def is_past(value, today=None):
    """Return True when the date is before today."""
    if value is None:
        return False
    due = parse_due_date(value)
    return due < (today or date.today())
