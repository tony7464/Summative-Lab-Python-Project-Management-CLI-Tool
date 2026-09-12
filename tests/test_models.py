"""Tests for Person, User, Project, Task, and their relationships."""

from datetime import date, timedelta

import pytest

from models import (
    DuplicateError,
    Entity,
    NotFoundError,
    Person,
    Project,
    Task,
    User,
    ValidationError,
    Workspace,
)


def test_user_inherits_from_person():
    user = User.create("Alex", "alex@foundry.dev")
    assert isinstance(user, Person)
    assert isinstance(user, Entity)
    assert user.id == 1
    assert "Alex" in str(user)
    assert "alex@foundry.dev" in repr(user)


def test_person_name_setter_validates():
    with pytest.raises(ValidationError):
        Person("")


def test_user_email_defaults_from_name():
    user = User.create("Sam Ortiz")
    assert user.email == "sam.ortiz@foundry.local"


def test_class_id_counters_are_per_type():
    User.create("Alex", "alex@foundry.dev")
    User.create("Maya", "maya@foundry.dev")
    Project.create("CLI Tool")
    assert [user.id for user in User.all()] == [1, 2]
    assert Project.all()[0].id == 1


def test_find_by_name_is_case_insensitive():
    User.create("Alex", "alex@foundry.dev")
    assert User.find_by_name("alex").email == "alex@foundry.dev"
    assert User.find_by_name("nobody") is None


def test_entity_find_by_id():
    user = User.create("Alex", "alex@foundry.dev")
    assert User.find(user.id) is user
    assert User.find("1") is user
    assert User.find("nope") is None
    assert User.find(99) is None
    assert hash(user) == hash(("User", user.id))


def test_user_project_one_to_many(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    first = workspace.add_project("Alex", "CLI Tool")
    second = workspace.add_project("Alex", "Docs Site")
    alex = User.find_by_name("Alex")
    assert alex.projects == [first, second]
    assert first.owner is alex


def test_project_task_one_to_many(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    task = workspace.add_task("CLI Tool", "Implement add-task")
    project = Project.find_by_title("CLI Tool")
    assert project.tasks == [task]
    assert task.project is project


def test_task_contributors_are_many_to_many(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_user("Maya", "maya@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    task = workspace.add_task("CLI Tool", "Implement add-task", assign="Alex")
    workspace.add_contributor("Implement add-task", "Maya")
    maya = User.find_by_name("Maya")
    assert maya in task.contributors
    assert task in maya.contributed_tasks


def test_project_progress_and_status_are_dynamic(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    project = workspace.add_project("Alex", "CLI Tool")
    assert project.status == "planning"
    assert project.progress == 0.0
    workspace.add_task("CLI Tool", "One")
    workspace.add_task("CLI Tool", "Two")
    workspace.complete_task("One")
    assert project.progress == 0.5
    assert project.status == "in_progress"
    workspace.complete_task("Two")
    assert project.is_complete
    assert project.status == "complete"


def test_overdue_project_status(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    yesterday = date.today() - timedelta(days=1)
    project = workspace.add_project("Alex", "Late Work", due_date=yesterday)
    workspace.add_task("Late Work", "Finish it")
    assert project.is_overdue()
    assert project.status == "overdue"
    workspace.complete_task("Finish it")
    assert not project.is_overdue()
    assert project.status == "complete"


def test_task_status_transitions():
    task = Task.create("Write tests")
    assert task.start()
    assert task.status == "in_progress"
    assert not task.start()
    assert task.complete()
    assert task.is_complete
    assert not task.complete()
    assert task.reopen()
    assert task.status == "todo"


def test_workload_counts_open_assigned_tasks(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_task("CLI Tool", "One", assign="Alex")
    workspace.add_task("CLI Tool", "Two", assign="Alex")
    workspace.complete_task("One")
    assert User.find_by_name("Alex").workload() == 1


def test_searchable_mixin(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool", "tracker work")
    workspace.add_task("CLI Tool", "Implement add-task")
    assert User.find_by_name("Alex").matches("foundry")
    assert Project.find_by_title("CLI Tool").matches("tracker")
    assert Task.find_by_title("Implement add-task")[0].matches("add-task")
    assert not User.find_by_name("Alex").matches("zzz")


def test_duplicate_user_and_project(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    with pytest.raises(DuplicateError):
        workspace.add_user("Alex", "other@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    with pytest.raises(DuplicateError):
        workspace.add_project("Alex", "CLI Tool")


def test_missing_user_raises(workspace):
    with pytest.raises(NotFoundError):
        workspace.get_user("Alex")


def test_ambiguous_task_title_requires_project(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_project("Alex", "Docs Site")
    workspace.add_task("CLI Tool", "Write README")
    workspace.add_task("Docs Site", "Write README")
    with pytest.raises(ValidationError, match="More than one task"):
        workspace.get_task("Write README")
    task = workspace.get_task("Write README", "Docs Site")
    assert task.project.title == "Docs Site"


def test_collaborator_cannot_be_owner(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    with pytest.raises(ValidationError):
        workspace.add_collaborator("CLI Tool", "Alex")


def test_remove_user_cascades_owned_work(workspace):
    workspace.add_user("Alex", "alex@foundry.dev")
    workspace.add_user("Maya", "maya@foundry.dev")
    workspace.add_project("Alex", "CLI Tool")
    workspace.add_task("CLI Tool", "Implement add-task", assign="Alex")
    workspace.add_collaborator("CLI Tool", "Maya")
    workspace.remove_user("Alex")
    assert User.find_by_name("Alex") is None
    assert Project.find_by_title("CLI Tool") is None
    assert Task.all() == []
    assert User.find_by_name("Maya").collaborations == []
