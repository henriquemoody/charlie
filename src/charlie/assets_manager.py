import shutil
from pathlib import Path

from charlie.tracker import Tracker


class AssetsManager:
    def __init__(self, tracker: Tracker):
        self.tracker = tracker

    def copy_assets(
        self,
        assets: list[str],
        source_base: Path,
        destination_base: Path,
    ) -> None:
        for asset in assets:
            asset_path = Path(asset)
            relative_path = asset_path.relative_to(source_base)
            destination = destination_base / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, destination)
            self.tracker.track(f"Created {destination}")
