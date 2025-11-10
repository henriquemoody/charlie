"""Event tracking for configuration generation progress."""

from typing import Any


class Tracker:
    """Tracks events during agent configuration generation.

    Follows Command-Query Separation:
    - track() is a command (modifies state)
    - records property is a query (returns state without modification)
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def track(self, event: str, **metadata: Any) -> None:
        """Record an event with optional metadata.

        Args:
            event: Description of the event
            **metadata: Additional event data
        """
        record = {"event": event}
        if metadata:
            record.update(metadata)
        self._records.append(record)

    @property
    def records(self) -> list[dict[str, Any]]:
        """Query all tracked records.

        Returns:
            List of event records
        """
        return self._records.copy()
