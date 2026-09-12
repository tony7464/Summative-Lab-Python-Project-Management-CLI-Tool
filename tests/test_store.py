"""Tests for JSON load/save, missing files, and malformed data."""

import json

import pytest

from models import Project, StorageError, Task, User, Workspace
from utils.hooks import HookBus
from utils.store import load, restore, save, snapshot


def test_save_and_load_round_trip(data_file, crew):
    crew.add_collaborator("CLI Tool", "Maya")
    crew.add_contributor("Implement add-task", "Maya")
    save(data_file)
    payload = json.loads(data_file.read_text())
    assert payload["users"][0]["name"] == "Alex"
    assert payload["projects"][0]["title"] == "CLI Tool"
    assert payload["tasks"][0]["title"] == "Implement add-task"

    loaded = load(data_file)
    assert isinstance(loaded, Workspace)
    alex = User.find_by_name("Alex")
    maya = User.find_by_name("Maya")
    project = Project.find_by_title("CLI Tool")
    task = Task.find_by_title("Implement add-task")[0]
    assert project.owner is alex
    assert maya in project.collaborators
    assert task.assigned_to is alex
    assert maya in task.contributors
    assert project.due_date.isoformat() == "2026-10-01"


def test_missing_file_starts_empty(data_file):
    workspace = load(data_file)
    assert User.all() == []
    assert Project.all() == []
    assert isinstance(workspace, Workspace)


def test_malformed_json_raises(data_file):
    data_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError, match="not valid JSON"):
        load(data_file)


def test_malformed_records_raise(data_file):
    data_file.write_text(json.dumps({"users": ["nope"]}), encoding="utf-8")
    with pytest.raises(StorageError, match="must be an object"):
        load(data_file)


def test_missing_user_name_is_malformed():
    with pytest.raises(StorageError, match="missing"):
        restore({"users": [{"id": 1, "email": "a@b.co"}]})


def test_non_object_payload_raises():
    with pytest.raises(StorageError, match="JSON object"):
        restore([])


def test_missing_required_keys_raise():
    with pytest.raises(StorageError, match="missing"):
        restore({"users": [{"id": 1}]})


def test_snapshot_uses_ids_not_objects(crew):
    payload = snapshot()
    assert "owner_id" in payload["projects"][0]
    assert "assigned_to_id" in payload["tasks"][0]


def test_hook_bus_runs_listeners():
    bus = HookBus()
    seen = []
    bus.register("after_change", lambda **payload: seen.append(payload["command"]))
    bus.emit("after_change", command="add-user")
    assert seen == ["add-user"]
    bus.clear()
    bus.emit("after_change", command="add-user")
    assert seen == ["add-user"]


def test_hook_bus_swallows_listener_errors():
    bus = HookBus()
    bus.register("after_change", lambda **_payload: (_ for _ in ()).throw(RuntimeError("boom")))
    bus.emit("after_change", command="add-user")
