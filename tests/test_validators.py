"""Tests for field cleaners and date parsing."""

from datetime import date

import pytest

from models import ValidationError
from utils.dates import format_due_date, is_past, parse_due_date
from utils.validators import (
    clean_description,
    clean_email,
    clean_name,
    clean_status,
    clean_title,
    email_from_name,
)


def test_clean_name_strips_spaces():
    assert clean_name("  Alex   Rivera  ") == "Alex Rivera"


def test_clean_name_rejects_blank():
    with pytest.raises(ValidationError):
        clean_name("   ")


def test_clean_name_rejects_short():
    with pytest.raises(ValidationError):
        clean_name("A")


def test_clean_email_normalizes_case():
    assert clean_email("Alex@Foundry.DEV") == "alex@foundry.dev"


def test_clean_email_rejects_invalid():
    with pytest.raises(ValidationError):
        clean_email("not-an-email")


def test_clean_title_and_description():
    assert clean_title("  CLI Tool  ") == "CLI Tool"
    assert clean_description(None) == ""
    with pytest.raises(ValidationError):
        clean_title("")


def test_clean_status_aliases():
    assert clean_status("complete") == "done"
    assert clean_status("doing") == "in_progress"
    assert clean_status("open") == "todo"
    with pytest.raises(ValidationError):
        clean_status("blocked")


def test_email_from_name():
    assert email_from_name("Alex Rivera") == "alex.rivera@foundry.local"


def test_parse_due_date_iso_and_written():
    assert parse_due_date("2026-10-01") == date(2026, 10, 1)
    assert parse_due_date("Oct 1 2026") == date(2026, 10, 1)
    assert parse_due_date(None) is None


def test_parse_due_date_rejects_garbage():
    with pytest.raises(ValidationError):
        parse_due_date("next sprint maybe")


def test_format_and_is_past():
    assert format_due_date(None) == "—"
    assert format_due_date(date(2026, 10, 1)) == "2026-10-01"
    assert is_past(date(2000, 1, 1), today=date(2026, 1, 1))
    assert not is_past(None)
