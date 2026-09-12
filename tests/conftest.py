"""Shared fixtures. Each test starts with an empty in-memory graph."""

import pytest

from models import Workspace, reset_all


@pytest.fixture(autouse=True)
def clean_registries():
    """Reset class registries before and after every test."""
    reset_all()
    yield
    reset_all()


@pytest.fixture
def workspace():
    """Return an empty Workspace."""
    return Workspace()


@pytest.fixture
def data_file(tmp_path):
    """Return a temp JSON path that does not exist yet."""
    return tmp_path / "tracker.json"


@pytest.fixture
def crew(workspace):
    """A small crew used by relationship and CLI tests."""
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_user("Maya", "maya@foundry.dev")
    workspace.add_project(
        "Alex",
        "CLI Tool",
        "Build the tracker",
        due_date="2026-10-01",
    )
    workspace.add_task("CLI Tool", "Implement add-task", assign="Alex")
    return workspace
