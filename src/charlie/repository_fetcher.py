"""Repository fetcher for cloning and updating Git repositories."""

import hashlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console()


class RepositoryFetchError(Exception):
    """Raised when a repository cannot be fetched."""

    pass


@dataclass
class ParsedRepository:
    """Parsed repository URL with optional version."""

    url: str
    version: str | None

    @property
    def cache_key(self) -> str:
        """Generate a unique cache key for this repository."""
        # Include the version in the hash input so different versions don't share a cache
        base = f"{self.url}#{self.version}" if self.version is not None else self.url
        url_hash = hashlib.sha256(base.encode()).hexdigest()[:16]
        # Extract a readable name from the URL
        name = _extract_repo_name(self.url)
        if self.version is not None:
            # Sanitize version for filesystem use and readability
            version_safe = re.sub(r"[^a-zA-Z0-9._-]", "-", self.version)
            return f"{name}-{version_safe}-{url_hash}"
        return f"{name}-{url_hash}"


def _extract_repo_name(url: str) -> str:
    """Extract a readable repository name from a Git URL.

    Examples:
        https://github.com/Org/repo-name -> repo-name
        git@github.com:Org/repo-name.git -> repo-name
    """
    # Remove .git suffix if present
    url = re.sub(r"\.git$", "", url)

    # Extract the last path component
    if "/" in url:
        name = url.rsplit("/", 1)[-1]
    elif ":" in url:
        # SSH format: git@github.com:Org/repo
        name = url.rsplit(":", 1)[-1].rsplit("/", 1)[-1]
    else:
        name = url

    # Sanitize the name for filesystem use
    name = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    return name or "repo"


def parse_repository_url(url: str) -> ParsedRepository:
    """Parse a repository URL that may include a version fragment.

    Format: <git-url>#<version>

    Examples:
        https://github.com/Org/Config#v1.0
        git@github.com:Org/Config.git#main
        https://github.com/Org/Config (no version, uses default branch)
    """
    if "#" in url:
        base_url, version = url.rsplit("#", 1)
        return ParsedRepository(url=base_url, version=version if version else None)

    return ParsedRepository(url=url, version=None)


def _get_cache_directory() -> Path:
    """Get the cache directory for cloned repositories."""
    cache_dir = Path(tempfile.gettempdir()) / "charlie-repos"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _run_git_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else e.stdout.strip()
        raise RepositoryFetchError(f"Git command failed: git {' '.join(args)}\n{error_message}")
    except FileNotFoundError:
        raise RepositoryFetchError("Git is not installed or not found in PATH")


def _clone_repository(url: str, target_dir: Path) -> None:
    """Clone a repository with shallow depth."""
    console.print(f"  [dim]Cloning {url}...[/dim]")
    _run_git_command(["clone", "--depth=1", url, str(target_dir)])


def _update_repository(repo_dir: Path, version: str | None = None) -> None:
    """Update an existing repository by fetching and resetting.

    Args:
        repo_dir: Path to the repository directory
        version: Optional specific version/ref to fetch. If None, fetches default branch.
    """
    if version:
        # For versioned refs, skip update and rely on checkout
        # This avoids issues with fetching the wrong branch
        return

    console.print(f"  [dim]Updating {repo_dir.name}...[/dim]")
    _run_git_command(["fetch", "--depth=1", "origin"], cwd=repo_dir)
    _run_git_command(["reset", "--hard", "FETCH_HEAD"], cwd=repo_dir)


def _checkout_version(repo_dir: Path, version: str) -> None:
    """Checkout a specific version (branch or tag)."""
    console.print(f"  [dim]Checking out {version}...[/dim]")
    # Fetch the specific ref with depth 1
    try:
        _run_git_command(["fetch", "--depth=1", "origin", version], cwd=repo_dir)
        _run_git_command(["checkout", "FETCH_HEAD"], cwd=repo_dir)
    except RepositoryFetchError:
        # Try as a tag
        try:
            _run_git_command(["fetch", "--depth=1", "origin", f"refs/tags/{version}:refs/tags/{version}"], cwd=repo_dir)
            _run_git_command(["checkout", f"tags/{version}"], cwd=repo_dir)
        except RepositoryFetchError as e:
            raise RepositoryFetchError(f"Could not checkout version '{version}': {e}")


def fetch_repository(repository_url: str) -> Path:
    """Fetch a repository and return the path to the local clone.

    If the repository is already cached, it will be updated.
    Supports version specification via URL fragment (e.g., url#v1.0).

    Args:
        repository_url: Git URL, optionally with #version suffix

    Returns:
        Path to the local repository directory

    Raises:
        RepositoryFetchError: If the repository cannot be fetched

    Security Note:
        This function clones Git repositories from the provided URLs without
        additional validation. Users should only use repository URLs from trusted
        sources, as malicious repositories could potentially contain harmful code
        or configuration.
    """
    parsed = parse_repository_url(repository_url)
    cache_dir = _get_cache_directory()
    repo_dir = cache_dir / parsed.cache_key

    if repo_dir.exists():
        try:
            _update_repository(repo_dir, parsed.version)
        except RepositoryFetchError:
            # If update fails, remove and re-clone
            console.print("  [yellow]Cache corrupted, re-cloning...[/yellow]")
            shutil.rmtree(repo_dir)
            _clone_repository(parsed.url, repo_dir)
    else:
        _clone_repository(parsed.url, repo_dir)

    # Checkout specific version if specified
    if parsed.version:
        _checkout_version(repo_dir, parsed.version)

    return repo_dir
