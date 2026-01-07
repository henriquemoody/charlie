import pytest

from charlie.assets_manager import AssetsManager
from charlie.tracker import Tracker


def test_should_copy_file_to_destination_when_single_asset_provided(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    asset_file = source_base / "file.txt"
    asset_file.write_text("content")
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(asset_file)], destination_base)

    destination_file = destination_base / "file.txt"
    assert destination_file.exists()
    assert destination_file.read_text() == "content"


def test_should_copy_all_files_to_destination_when_multiple_assets_provided(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    file1 = source_base / "file1.txt"
    file2 = source_base / "file2.json"
    file1.write_text("content1")
    file2.write_text('{"key": "value"}')
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(file1), str(file2)], destination_base)

    assert (destination_base / "file1.txt").exists()
    assert (destination_base / "file2.json").exists()
    assert (destination_base / "file1.txt").read_text() == "content1"
    assert (destination_base / "file2.json").read_text() == '{"key": "value"}'


def test_should_preserve_directory_structure_when_copying_nested_assets(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    images_dir = source_base / "images"
    icons_dir = images_dir / "icons"
    images_dir.mkdir(parents=True)
    icons_dir.mkdir(parents=True)
    file1 = source_base / "root.txt"
    file2 = images_dir / "logo.png"
    file3 = icons_dir / "favicon.ico"
    file1.write_text("root")
    file2.write_text("png")
    file3.write_text("ico")
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(file1), str(file2), str(file3)], destination_base)

    assert (destination_base / "root.txt").exists()
    assert (destination_base / "images" / "logo.png").exists()
    assert (destination_base / "images" / "icons" / "favicon.ico").exists()
    assert (destination_base / "root.txt").read_text() == "root"
    assert (destination_base / "images" / "logo.png").read_text() == "png"
    assert (destination_base / "images" / "icons" / "favicon.ico").read_text() == "ico"


def test_should_create_destination_directories_when_they_do_not_exist(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    nested_dir = source_base / "level1" / "level2" / "level3"
    nested_dir.mkdir(parents=True)
    asset_file = nested_dir / "deep.txt"
    asset_file.write_text("deep content")
    destination_base = tmp_path / "destination" / "some" / "nested" / "path"

    manager.copy_assets([str(asset_file)], destination_base)

    destination_file = destination_base / "level1" / "level2" / "level3" / "deep.txt"
    assert destination_file.exists()
    assert destination_file.read_text() == "deep content"


def test_should_do_nothing_when_empty_assets_list_provided(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    destination_base = tmp_path / "destination"

    manager.copy_assets([], destination_base)

    assert len(tracker.records) == 0


def test_should_track_each_file_when_copying_multiple_assets(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    files = [source_base / f"file{i}.txt" for i in range(5)]
    for file in files:
        file.write_text(f"content {file.name}")
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(f) for f in files], destination_base)

    assert len(tracker.records) == 5
    tracked_events = [record["event"] for record in tracker.records]
    for i in range(5):
        expected_dest = destination_base / f"file{i}.txt"
        assert f"Created {expected_dest}" in tracked_events


def test_should_track_copied_file_when_single_asset_provided(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    asset_file = source_base / "file.txt"
    asset_file.write_text("content")
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(asset_file)], destination_base)

    assert len(tracker.records) == 1
    destination_file = destination_base / "file.txt"
    assert tracker.records[0]["event"] == f"Created {destination_file}"


def test_should_preserve_binary_content_when_copying_file(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    asset_file = source_base / "data.bin"
    test_content = b"\x00\x01\x02\xff\xfe\xfd"
    asset_file.write_bytes(test_content)
    destination_base = tmp_path / "destination"

    manager.copy_assets([str(asset_file)], destination_base)

    destination_file = destination_base / "data.bin"
    assert destination_file.read_bytes() == test_content


def test_should_overwrite_existing_file_when_copying_to_same_location(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    asset_file = source_base / "file.txt"
    asset_file.write_text("new content")
    destination_base = tmp_path / "destination" / "assets"
    destination_base.mkdir(parents=True)
    existing_file = destination_base / "file.txt"
    existing_file.write_text("old content")

    manager.copy_assets([str(asset_file)], destination_base)

    assert existing_file.read_text() == "new content"


def test_should_preserve_file_permissions_when_copying_asset(tmp_path) -> None:
    tracker = Tracker()
    manager = AssetsManager(tracker)
    source_base = tmp_path / "source" / ".charlie" / "assets"
    source_base.mkdir(parents=True)
    asset_file = source_base / "script.sh"
    asset_file.write_text("#!/bin/bash\necho 'test'")
    asset_file.chmod(0o755)
    destination_base = tmp_path / "destination" / "assets"

    manager.copy_assets([str(asset_file)], destination_base)

    destination_file = destination_base / "script.sh"
    assert destination_file.stat().st_mode == asset_file.stat().st_mode


def test_should_copy_assets_from_multiple_source_directories(tmp_path) -> None:
    """Test that assets from different source directories (e.g., extended repos) are copied correctly."""
    tracker = Tracker()
    manager = AssetsManager(tracker)

    # Simulate local project assets
    local_source = tmp_path / "local" / ".charlie" / "assets"
    local_source.mkdir(parents=True)
    local_file = local_source / "local.txt"
    local_file.write_text("local content")

    # Simulate extended repository assets (in temp dir)
    extended_source = tmp_path / "charlie-repos" / "extended-config" / ".charlie" / "assets"
    extended_source.mkdir(parents=True)
    extended_file = extended_source / "extended.txt"
    extended_file.write_text("extended content")

    # Simulate another extended repository with nested structure
    another_source = tmp_path / "charlie-repos" / "another-config" / ".charlie" / "assets"
    scripts_dir = another_source / "scripts"
    scripts_dir.mkdir(parents=True)
    script_file = scripts_dir / "deploy.sh"
    script_file.write_text("#!/bin/bash\ndeploy")

    destination_base = tmp_path / "output" / "assets"

    # Mix assets from all sources
    manager.copy_assets(
        [str(local_file), str(extended_file), str(script_file)],
        destination_base,
    )

    assert (destination_base / "local.txt").exists()
    assert (destination_base / "local.txt").read_text() == "local content"
    assert (destination_base / "extended.txt").exists()
    assert (destination_base / "extended.txt").read_text() == "extended content"
    assert (destination_base / "scripts" / "deploy.sh").exists()
    assert (destination_base / "scripts" / "deploy.sh").read_text() == "#!/bin/bash\ndeploy"


def test_should_raise_error_when_asset_path_does_not_contain_marker(tmp_path) -> None:
    """Test that a proper error is raised when an asset path doesn't follow the expected pattern."""
    tracker = Tracker()
    manager = AssetsManager(tracker)

    # Create an asset file outside the expected structure
    invalid_source = tmp_path / "invalid" / "assets"
    invalid_source.mkdir(parents=True)
    invalid_file = invalid_source / "file.txt"
    invalid_file.write_text("content")

    destination_base = tmp_path / "destination"

    with pytest.raises(ValueError, match="does not contain '.charlie/assets'"):
        manager.copy_assets([str(invalid_file)], destination_base)
