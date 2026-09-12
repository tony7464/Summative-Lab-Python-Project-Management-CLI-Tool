# Foundry

Command-line project tracker for a small software crew.

Admins add people, hang projects on a person, and break the work into tasks. Everything saves to a local JSON file, so you can close the terminal and pick it back up.

This is my Flatiron summative lab: OOP models, an argparse CLI, file persistence, PyPI packages, and a pytest suite.

## What it does

- Create, list, edit, and remove users
- Add projects to a user and show the projects tied to that person
- Add tasks to a project, assign them, add contributors, and mark them complete
- Search users, projects, and tasks
- Show a dashboard with progress bars and overdue work
- Persist the whole graph in `data/tracker.json`

## Object model

```
Person
 └── User
        │ owns
        ▼
     Project ────── collaborates ────── User
        │
        │ has
        ▼
      Task  ── assigned_to ──► User
        │
        └── contributors ──► User   (many-to-many)
```

- **One-to-many:** a user owns many projects. A project owns many tasks.
- **Many-to-many:** a task can have several contributors, and a user can contribute to several tasks. Projects can also pick up collaborators who are not the owner.
- **Inheritance:** `User` extends `Person`. Both sit on `Entity`, which owns the ID counter, the in-memory registry, and timestamps.
- **Encapsulation:** name, email, title, status, and due date go through `@property` setters.
- **Dynamic behavior:** project `status` and `progress` are computed from tasks and the due date. Completing the last task flips the project to complete.

## Project layout

```
.
├── main.py              CLI entry point
├── models/              Person, User, Project, Task, Workspace
├── cli/                 argparse parser and command handlers
├── utils/               validation, dates, JSON store, hooks, display
├── data/                tracker.json is created on the first write
├── tests/               pytest coverage for models, store, and CLI
├── requirements.txt
└── Pipfile
```

## Setup

Python 3.10 or newer.

```bash
git clone https://github.com/tony7464/Summative-Lab-Python-Project-Management-CLI-Tool.git
cd Summative-Lab-Python-Project-Management-CLI-Tool
```

### pip

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### pipenv

```bash
pipenv install --dev
pipenv shell
```

Packages in play:

- **rich** — tables, panels, and status colors
- **python-dateutil** — due dates like `2026-10-01` or `Oct 1 2026`
- **tabulate** — `--plain` tables you can pipe or paste
- **pytest** / **pytest-cov** — the test suite

## Run the CLI

```bash
python main.py
```

That prints the Foundry banner and the command list.

The assignment examples work as written:

```bash
python main.py add-user --name "Alex"
python main.py add-project --user "Alex" --title "CLI Tool"
python main.py add-task --project "CLI Tool" --title "Implement add-task"
python main.py complete-task --title "Implement add-task"
python main.py list-projects --user "Alex"
```

Load a demo crew if you want something to click through:

```bash
python main.py seed
python main.py dashboard
```

## Command list

### Users

```bash
python main.py add-user --name "Maya Chen" --email maya@foundry.dev
python main.py list-users
python main.py show-user --name "Maya Chen"
python main.py edit-user --name "Maya Chen" --email maya@studio.dev
python main.py remove-user --name "Maya Chen"
```

`--email` is optional. If you skip it, Foundry stores `maya.chen@foundry.local`.

### Projects

```bash
python main.py add-project --user "Maya Chen" --title "Portfolio Site" --description "Freelance case studies" --due 2026-10-01
python main.py list-projects
python main.py list-projects --user "Maya Chen"
python main.py show-project --title "Portfolio Site"
python main.py edit-project --title "Portfolio Site" --due "Oct 15 2026"
python main.py search-projects --query portfolio
python main.py add-collaborator --project "Portfolio Site" --user "Alex"
python main.py remove-project --title "Portfolio Site"
```

### Tasks

```bash
python main.py add-task --project "Portfolio Site" --title "Design project grid" --assign "Maya Chen"
python main.py list-tasks --project "Portfolio Site"
python main.py start-task --title "Design project grid"
python main.py complete-task --title "Design project grid"
python main.py assign-task --title "Design project grid" --user "Alex"
python main.py add-contributor --title "Design project grid" --user "Sam Ortiz"
python main.py edit-task --title "Design project grid" --status in_progress
python main.py reopen-task --title "Design project grid"
python main.py remove-task --title "Design project grid"
```

If two projects share a task title, pass `--project` so Foundry knows which one you mean.

### Reports

```bash
python main.py dashboard
python main.py overdue
python main.py search --query CLI
```

### Helpful flags

| Flag | What it does |
| --- | --- |
| `--plain` | Print list tables with tabulate instead of Rich |
| `--data path.json` | Use a different JSON file |
| `-v` / `--verbose` | Write debug lines to `data/tracker.log` |

`--data` and `-v` go before the subcommand:

```bash
python main.py --data /tmp/demo.json seed
python main.py -v list-users
```

## Persistence

The graph lives in `data/tracker.json`. A write goes to a temp file first, then replaces the real file, so a crash mid-save should not leave you with half a JSON document.

Missing files start an empty store. Bad JSON or a record missing a required field raises a clear error instead of a stack trace.

Logs go to `data/tracker.log`. I used that file while I chased load/save bugs and command routing.

## Tests

```bash
pytest
pytest --cov=models --cov=cli --cov=utils --cov-report=term-missing
```

The suite covers:

- inheritance and property validation
- user → project and project → task relationships
- contributors as a many-to-many
- computed progress / overdue status
- JSON round-trips, missing files, and malformed data
- CLI happy paths and friendly errors, including the assignment examples

Tests write to a temp directory. They do not touch `data/tracker.json`.

## How the pieces talk

`main.py` calls `cli.app.main`. The parser in `cli/parser.py` wires each subcommand to a handler. Handlers call `Workspace`, which owns the relationship rules. `utils/store.py` reloads the graph from JSON at the start of a command and saves after a mutation. `utils/hooks.py` is a small event bus. After a successful write it logs the command that triggered the save.

I kept display code in `utils/display.py` so the handlers do not build Rich tables themselves.

## Known issues

- Project titles have to be unique. The CLI looks projects up by title, not by id.
- Task titles have to be unique inside a project. The same title on two projects needs `--project`.
- One JSON file. Two terminals saving at the same time can overwrite each other.
- No login. Anyone who can run the command can change the data.
- Due dates are calendar dates, not times.

## Notes

I started with the object graph, then persistence, then the CLI. The tests were the checklist. If a relationship looked wrong in `show-project`, I fixed it on the model, not in the printer.

`Entity` exists so User, Project, and Task do not each invent their own ID counter. `Workspace` exists so the CLI does not reach into `_registry` lists. That split is what I would keep if this ever grew a Flask API on top of the same classes.
