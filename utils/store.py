"""Load and save the workspace as a single JSON file."""

import json
from pathlib import Path

from models.exceptions import StorageError
from models.project import Project
from models.task import Task
from models.user import User
from models.workspace import Workspace, reset_all
from utils.logger import get_logger


def default_data_path():
    """Return the default JSON path under data/."""
    return Path(__file__).resolve().parent.parent / "data" / "tracker.json"


def snapshot():
    """Dump the in-memory graph to a JSON-safe dictionary."""
    return {
        "users": [user.to_dict() for user in User.all()],
        "projects": [project.to_dict() for project in Project.all()],
        "tasks": [task.to_dict() for task in Task.all()],
    }


def restore(payload):
    """Rebuild objects and wire relationships from a snapshot dict."""
    if not isinstance(payload, dict):
        raise StorageError("Data file must be a JSON object.")

    reset_all()
    users_by_id = {}
    for record in payload.get("users") or []:
        _require_keys(record, ("name",), "user")
        user = User.from_dict(record)
        users_by_id[user.id] = user

    projects_by_id = {}
    for record in payload.get("projects") or []:
        _require_keys(record, ("title",), "project")
        project = Project.from_dict(record)
        owner = users_by_id.get(record.get("owner_id"))
        if owner is not None:
            owner.add_project(project)
        for collaborator_id in record.get("collaborator_ids") or []:
            collaborator = users_by_id.get(collaborator_id)
            if collaborator is not None:
                project.add_collaborator(collaborator)
        projects_by_id[project.id] = project

    for record in payload.get("tasks") or []:
        _require_keys(record, ("title",), "task")
        task = Task.from_dict(record)
        project = projects_by_id.get(record.get("project_id"))
        if project is not None:
            project.add_task(task)
        assignee = users_by_id.get(record.get("assigned_to_id"))
        if assignee is not None:
            task.assign_to(assignee)
        for contributor_id in record.get("contributor_ids") or []:
            contributor = users_by_id.get(contributor_id)
            if contributor is not None:
                task.add_contributor(contributor)

    return Workspace()


def load(path):
    """Read a JSON file. Missing files start an empty workspace."""
    logger = get_logger()
    path = Path(path)
    if not path.exists():
        logger.warning("No data file at %s; starting empty.", path)
        reset_all()
        return Workspace()

    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"{path} is not valid JSON ({exc.msg} at line {exc.lineno})."
        ) from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc}") from exc

    try:
        workspace = restore(payload)
    except (TypeError, KeyError, ValueError) as exc:
        raise StorageError(f"{path} has malformed records: {exc}") from exc

    logger.info(
        "Loaded %s users, %s projects, %s tasks from %s",
        len(User.all()),
        len(Project.all()),
        len(Task.all()),
        path,
    )
    return workspace


def save(path):
    """Write the current graph to disk using a temp file, then replace."""
    logger = get_logger()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    payload = snapshot()

    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        tmp_path.replace(path)
    except OSError as exc:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                logger.debug("Could not remove temp file %s", tmp_path)
        raise StorageError(f"Could not save {path}: {exc}") from exc

    logger.info("Saved tracker data to %s", path)
    return path


def _require_keys(record, keys, label):
    """Raise StorageError when a required field is missing from a record."""
    if not isinstance(record, dict):
        raise StorageError(f"Each {label} record must be an object.")
    missing = [key for key in keys if key not in record]
    if missing:
        raise StorageError(
            f"{label.title()} record is missing: {', '.join(missing)}."
        )
