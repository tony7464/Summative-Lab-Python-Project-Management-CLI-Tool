"""Extra workspace tests for edit, search, seed, and task filters."""

from datetime import date, timedelta

import pytest

from models import Project, Task, User, ValidationError


def test_edit_user_and_project(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool", "first pass")
    workspace.edit_user("Alex", new_name="Alex Rivera", email="alex.r@foundry.dev")
    workspace.edit_project(
        "CLI Tool",
        new_title="Foundry CLI",
        description="second pass",
        due_date="2026-11-01",
    )
    assert User.find_by_name("Alex Rivera").email == "alex.r@foundry.dev"
    project = Project.find_by_title("Foundry CLI")
    assert project.description == "second pass"
    assert project.due_date.isoformat() == "2026-11-01"


def test_list_tasks_filters(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_user("Maya", "maya@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_project("Maya", "Portfolio Site")
    workspace.add_task("CLI Tool", "Implement add-task", assign="Alex")
    workspace.add_task("Portfolio Site", "Write copy", assign="Maya")
    workspace.complete_task("Write copy")
    assert len(workspace.list_tasks(project_title="CLI Tool")) == 1
    assert len(workspace.list_tasks(user_name="Maya")) == 1
    assert len(workspace.list_tasks(status="done")) == 1


def test_search_requires_query(workspace):
    with pytest.raises(ValidationError):
        workspace.search("   ")


def test_search_groups_hits(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_task("CLI Tool", "Implement add-task")
    results = workspace.search("CLI")
    assert results["projects"][0].title == "CLI Tool"
    assert results["tasks"][0].title == "Implement add-task"


def test_seed_builds_demo_relationships(workspace):
    demo = workspace.seed()
    assert len(demo["users"]) == 3
    cli = Project.find_by_title("CLI Tool")
    assert User.find_by_name("Maya Chen") in cli.collaborators
    persist = Task.find_by_title("Wire up JSON persistence")[0]
    assert persist.is_complete
    portfolio = Project.find_by_title("Portfolio Site")
    assert portfolio.is_overdue()
    assert workspace.overdue_projects() == [portfolio]


def test_seed_refuses_existing_data(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    with pytest.raises(ValidationError):
        workspace.seed()
    workspace.seed(force=True)
    assert User.find_by_name("Alex") is None
    assert User.find_by_name("Alex Rivera") is not None


def test_start_and_reopen(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_task("CLI Tool", "Implement add-task")
    workspace.start_task("Implement add-task")
    assert Task.find_by_title("Implement add-task")[0].status == "in_progress"
    workspace.complete_task("Implement add-task")
    workspace.reopen_task("Implement add-task")
    assert Task.find_by_title("Implement add-task")[0].status == "todo"


def test_remove_project_and_task(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_task("CLI Tool", "Implement add-task", assign="Alex")
    workspace.remove_task("Implement add-task")
    assert Task.all() == []
    workspace.remove_project("CLI Tool")
    assert Project.all() == []
    assert User.find_by_name("Alex").projects == []


def test_overdue_empty_when_no_due_date(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    assert workspace.overdue_projects() == []
    later = date.today() + timedelta(days=10)
    workspace.edit_project("CLI Tool", due_date=later)
    assert workspace.overdue_projects() == []
