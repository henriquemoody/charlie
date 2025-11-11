from typing import Any


class Tracker:
    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def track(self, event: str, metadata: dict[str, Any] | None = None) -> None:
        record = {**metadata, "event": event} if metadata else {"event": event}
        self._records.append(record)

    @property
    def records(self) -> list[dict[str, Any]]:
        return self._records.copy()
