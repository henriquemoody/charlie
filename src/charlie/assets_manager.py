import shutil
from pathlib import Path

from charlie.tracker import Tracker

ASSETS_DIR_MARKER = (".charlie", "assets")


class AssetsManager:
    def __init__(self, tracker: Tracker):
        self.tracker = tracker

    def _extract_relative_path(self, asset_path: Path) -> Path:
        parts = asset_path.parts

        marker_start_index = None
        for i in range(len(parts) - 1):
            if parts[i] == ASSETS_DIR_MARKER[0] and parts[i + 1] == ASSETS_DIR_MARKER[1]:
                marker_start_index = i
                break

        if marker_start_index is None:
            marker_str = f"{ASSETS_DIR_MARKER[0]}/{ASSETS_DIR_MARKER[1]}"
            raise ValueError(f"Asset path does not contain '{marker_str}': {asset_path}")

        relative_parts = parts[marker_start_index + 2 :]
        if not relative_parts:
            raise ValueError(f"Asset path has no file after '.charlie/assets': {asset_path}")
        return Path(*relative_parts)

    def copy_assets(
        self,
        assets: list[str],
        destination_base: Path,
    ) -> None:
        for asset in assets:
            asset_path = Path(asset)
            relative_path = self._extract_relative_path(asset_path)
            destination = destination_base / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, destination)
            self.tracker.track(f"Created {destination}")
