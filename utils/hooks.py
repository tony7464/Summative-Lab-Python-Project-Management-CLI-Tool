"""Tiny event bus used as save and mutation hooks."""

from utils.logger import get_logger


class HookBus:
    """Register functions and fire them after named events.

    The CLI uses this so a successful mutation always triggers a save
    without the command handlers talking to the file layer directly.
    """

    def __init__(self):
        self._listeners = {}

    def register(self, event, callback):
        """Attach a callback to an event name such as after_change."""
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, **payload):
        """Call every listener for this event. Errors are logged, not raised."""
        logger = get_logger()
        for callback in self._listeners.get(event, []):
            try:
                callback(**payload)
            except Exception as exc:  # noqa: BLE001 - hooks should not crash the CLI
                logger.exception("Hook for '%s' failed: %s", event, exc)

    def clear(self):
        """Remove every listener. Used by tests."""
        self._listeners.clear()
