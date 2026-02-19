"""
Git context detection for flaky cloud uploads.
"""

import subprocess
from dataclasses import dataclass


@dataclass
class GitContext:
    """Git context for the current working directory."""

    branch: str
    commit_sha: str
    has_remote: bool

    @property
    def branch_type(self) -> str:
        """Returns 'origin' if branch has remote tracking, 'local' otherwise."""
        return "origin" if self.has_remote else "local"

    @property
    def full_branch(self) -> str:
        """Returns the full branch identifier (e.g., 'origin/main' or 'local/feature-x')."""
        return f"{self.branch_type}/{self.branch}"


def _run_git_command(args: list[str]) -> str | None:
    """Run a git command and return stdout, or None if it fails."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_git_context() -> GitContext:
    """
    Detect git context for the current working directory.

    Returns a GitContext with:
    - branch: current branch name
    - commit_sha: current commit SHA (short)
    - has_remote: whether the branch has a remote tracking branch

    If git is not available or not in a repo, returns defaults.
    """
    branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch is None:
        return GitContext(branch="unknown", commit_sha="unknown", has_remote=False)

    commit_sha = _run_git_command(["rev-parse", "--short", "HEAD"]) or "unknown"

    upstream = _run_git_command(["rev-parse", "--abbrev-ref", "@{upstream}"])
    has_remote = upstream is not None

    return GitContext(
        branch=branch,
        commit_sha=commit_sha,
        has_remote=has_remote,
    )
