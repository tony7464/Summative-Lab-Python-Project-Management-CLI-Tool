"""CLI entry: parse args, load data, run a command, save on mutations."""

import logging
import sys
from pathlib import Path

from cli.parser import build_parser
from models import TrackerError
from utils import display
from utils.hooks import HookBus
from utils.logger import get_logger, setup_logging
from utils.store import default_data_path, load, save

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "data" / "tracker.log"


def main(argv=None, data_path=None):
    """Run one CLI command. Returns an exit code."""
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        display.banner()
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    path = Path(data_path or args.data_path or default_data_path())
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(DEFAULT_LOG if path == default_data_path() else path.with_suffix(".log"), log_level)
    logger = get_logger()
    logger.debug("Command: %s", " ".join(argv))

    try:
        workspace = load(path)
    except TrackerError as exc:
        display.error(str(exc))
        logger.error("Load failed: %s", exc)
        return 1

    hooks = HookBus()
    hooks.register(
        "after_change",
        lambda **payload: logger.info("Saved after %s", payload.get("command")),
    )

    try:
        args.func(args, workspace)
        if getattr(args, "mutating", False):
            save(path)
            hooks.emit("after_change", command=args.command)
    except TrackerError as exc:
        display.error(str(exc))
        logger.error("Command %s failed: %s", args.command, exc)
        return 1

    return 0
