from typing import Any


class Tracker:
    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def track(self, event: str, **metadata: Any) -> None:
        record = {"event": event}
        if metadata:
            record.update(metadata)
        self._records.append(record)

    @property
    def records(self) -> list[dict[str, Any]]:
        return self._records.copy()
