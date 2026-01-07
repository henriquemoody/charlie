from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from charlie.repository_fetcher import (
    ParsedRepository,
    RepositoryFetchError,
    _checkout_version,
    _clone_repository,
    _extract_repo_name,
    _run_git_command,
    _update_repository,
    fetch_repository,
    parse_repository_url,
)


def test_should_parse_https_url_without_version_when_no_fragment_provided() -> None:
    result = parse_repository_url("https://github.com/Org/repo-name")

    assert result.url == "https://github.com/Org/repo-name"
    assert result.version is None


def test_should_parse_https_url_with_version_when_fragment_provided() -> None:
    result = parse_repository_url("https://github.com/Org/repo-name#v1.0.0")

    assert result.url == "https://github.com/Org/repo-name"
    assert result.version == "v1.0.0"


def test_should_parse_ssh_url_without_version_when_no_fragment_provided() -> None:
    result = parse_repository_url("git@github.com:Org/repo-name.git")

    assert result.url == "git@github.com:Org/repo-name.git"
    assert result.version is None


def test_should_parse_ssh_url_with_version_when_fragment_provided() -> None:
    result = parse_repository_url("git@github.com:Org/repo-name.git#main")

    assert result.url == "git@github.com:Org/repo-name.git"
    assert result.version == "main"


def test_should_handle_empty_version_when_fragment_is_empty() -> None:
    result = parse_repository_url("https://github.com/Org/repo#")

    assert result.url == "https://github.com/Org/repo"
    assert result.version is None


def test_should_extract_repo_name_from_https_url() -> None:
    name = _extract_repo_name("https://github.com/Org/my-repo-name")

    assert name == "my-repo-name"


def test_should_extract_repo_name_from_https_url_with_git_suffix() -> None:
    name = _extract_repo_name("https://github.com/Org/my-repo-name.git")

    assert name == "my-repo-name"


def test_should_extract_repo_name_from_ssh_url() -> None:
    name = _extract_repo_name("git@github.com:Org/my-repo-name.git")

    assert name == "my-repo-name"


def test_should_sanitize_special_characters_in_repo_name() -> None:
    name = _extract_repo_name("https://github.com/Org/my.repo@name")

    assert name == "my-repo-name"


def test_should_generate_unique_cache_key_for_different_urls() -> None:
    repo1 = ParsedRepository(url="https://github.com/Org/repo1", version=None)
    repo2 = ParsedRepository(url="https://github.com/Org/repo2", version=None)

    assert repo1.cache_key != repo2.cache_key


def test_should_generate_same_cache_key_for_same_url() -> None:
    repo1 = ParsedRepository(url="https://github.com/Org/repo", version=None)
    repo2 = ParsedRepository(url="https://github.com/Org/repo", version=None)

    assert repo1.cache_key == repo2.cache_key


def test_should_include_readable_name_in_cache_key() -> None:
    repo = ParsedRepository(url="https://github.com/Org/my-cool-repo", version=None)

    assert "my-cool-repo" in repo.cache_key


def test_should_generate_different_cache_key_for_different_versions() -> None:
    """Different versions of the same repository should have different cache keys.

    This ensures that switching between versions doesn't corrupt the cache.
    """
    repo1 = ParsedRepository(url="https://github.com/Org/repo", version="v1.0")
    repo2 = ParsedRepository(url="https://github.com/Org/repo", version="v2.0")

    assert repo1.cache_key != repo2.cache_key
    assert "v1.0" in repo1.cache_key or "v1-0" in repo1.cache_key
    assert "v2.0" in repo2.cache_key or "v2-0" in repo2.cache_key


# Integration tests for Git operations


def test_should_raise_error_when_git_command_fails() -> None:
    """Test that _run_git_command raises RepositoryFetchError on command failure."""
    with pytest.raises(RepositoryFetchError, match="Git command failed"):
        _run_git_command(["invalid-command"])


def test_should_raise_error_when_git_not_installed(tmp_path: Path) -> None:
    """Test that _run_git_command raises RepositoryFetchError when git is not found."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RepositoryFetchError, match="Git is not installed"):
            _run_git_command(["status"])


@patch("charlie.repository_fetcher._run_git_command")
def test_should_clone_repository_with_shallow_depth(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _clone_repository calls git clone with correct arguments."""
    url = "https://github.com/test/repo"
    target_dir = tmp_path / "test-repo"

    _clone_repository(url, target_dir)

    mock_git.assert_called_once()
    args = mock_git.call_args[0][0]
    assert args[0] == "clone"
    assert "--depth=1" in args
    assert url in args
    assert str(target_dir) in args


@patch("charlie.repository_fetcher._run_git_command")
def test_should_update_repository_without_version(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _update_repository fetches and resets when no version is specified."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    _update_repository(repo_dir, version=None)

    assert mock_git.call_count == 2
    # First call: fetch
    fetch_call = mock_git.call_args_list[0]
    assert "fetch" in fetch_call[0][0]
    assert "--depth=1" in fetch_call[0][0]
    # Second call: reset
    reset_call = mock_git.call_args_list[1]
    assert "reset" in reset_call[0][0]
    assert "--hard" in reset_call[0][0]


@patch("charlie.repository_fetcher._run_git_command")
def test_should_skip_update_when_version_specified(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _update_repository skips update when a version is specified."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    _update_repository(repo_dir, version="v1.0")

    # Should not call git at all
    mock_git.assert_not_called()


@patch("charlie.repository_fetcher._run_git_command")
def test_should_checkout_branch_version(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _checkout_version fetches and checks out a branch."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    _checkout_version(repo_dir, "main")

    assert mock_git.call_count == 2
    # First call: fetch specific ref
    fetch_call = mock_git.call_args_list[0]
    assert "fetch" in fetch_call[0][0]
    assert "main" in fetch_call[0][0]
    # Second call: checkout
    checkout_call = mock_git.call_args_list[1]
    assert "checkout" in checkout_call[0][0]


@patch("charlie.repository_fetcher._run_git_command")
def test_should_try_tag_when_branch_checkout_fails(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _checkout_version tries to fetch as a tag when branch fetch fails."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # First fetch (branch) fails, second fetch (tag) succeeds
    mock_git.side_effect = [
        RepositoryFetchError("Branch not found"),  # fetch branch fails
        None,  # fetch tag succeeds
        None,  # checkout succeeds
    ]

    _checkout_version(repo_dir, "v1.0")

    assert mock_git.call_count == 3
    # Should try fetching as tag
    tag_fetch_call = mock_git.call_args_list[1]
    assert "refs/tags/v1.0:refs/tags/v1.0" in tag_fetch_call[0][0]


@patch("charlie.repository_fetcher._run_git_command")
def test_should_raise_error_when_version_not_found(mock_git: MagicMock, tmp_path: Path) -> None:
    """Test that _checkout_version raises error when version cannot be checked out."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    # Both branch and tag fetches fail
    mock_git.side_effect = [
        RepositoryFetchError("Branch not found"),
        RepositoryFetchError("Tag not found"),
    ]

    with pytest.raises(RepositoryFetchError, match="Could not checkout version"):
        _checkout_version(repo_dir, "invalid-version")


@patch("charlie.repository_fetcher._clone_repository")
@patch("charlie.repository_fetcher._get_cache_directory")
def test_should_clone_when_repo_not_cached(mock_cache_dir: MagicMock, mock_clone: MagicMock, tmp_path: Path) -> None:
    """Test that fetch_repository clones when repository is not in cache."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    mock_cache_dir.return_value = cache_dir
    url = "https://github.com/test/repo"

    # Mock clone to create the directory
    def create_repo_dir(url, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)

    mock_clone.side_effect = create_repo_dir

    result = fetch_repository(url)

    mock_clone.assert_called_once()
    assert url in str(mock_clone.call_args)
    assert result.exists()


@patch("charlie.repository_fetcher._update_repository")
@patch("charlie.repository_fetcher._get_cache_directory")
def test_should_update_when_repo_already_cached(
    mock_cache_dir: MagicMock, mock_update: MagicMock, tmp_path: Path
) -> None:
    """Test that fetch_repository updates when repository is already cached."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    mock_cache_dir.return_value = cache_dir

    # Create a fake cached repo
    parsed = parse_repository_url("https://github.com/test/repo")
    repo_dir = cache_dir / parsed.cache_key
    repo_dir.mkdir()

    result = fetch_repository("https://github.com/test/repo")

    mock_update.assert_called_once()
    assert result == repo_dir


@patch("charlie.repository_fetcher._clone_repository")
@patch("charlie.repository_fetcher._update_repository")
@patch("charlie.repository_fetcher._get_cache_directory")
def test_should_reclone_when_update_fails(
    mock_cache_dir: MagicMock, mock_update: MagicMock, mock_clone: MagicMock, tmp_path: Path
) -> None:
    """Test that fetch_repository re-clones when update fails (corrupted cache)."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    mock_cache_dir.return_value = cache_dir

    # Create a fake cached repo
    parsed = parse_repository_url("https://github.com/test/repo")
    repo_dir = cache_dir / parsed.cache_key
    repo_dir.mkdir()
    (repo_dir / "marker.txt").write_text("corrupted")

    # Make update fail
    mock_update.side_effect = RepositoryFetchError("Update failed")

    fetch_repository("https://github.com/test/repo")

    # Should have removed the corrupted cache and cloned
    mock_clone.assert_called_once()
    assert not (repo_dir / "marker.txt").exists()  # Old cache was deleted


@patch("charlie.repository_fetcher._checkout_version")
@patch("charlie.repository_fetcher._clone_repository")
@patch("charlie.repository_fetcher._get_cache_directory")
def test_should_checkout_version_after_clone(
    mock_cache_dir: MagicMock, mock_clone: MagicMock, mock_checkout: MagicMock, tmp_path: Path
) -> None:
    """Test that fetch_repository checks out specific version when provided."""
    mock_cache_dir.return_value = tmp_path
    url = "https://github.com/test/repo#v1.0"

    fetch_repository(url)

    mock_clone.assert_called_once()
    mock_checkout.assert_called_once()
    checkout_args = mock_checkout.call_args
    assert "v1.0" in str(checkout_args)
