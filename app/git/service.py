"""Git service — clone/pull repositories and write PR/MR inline comments."""

import os
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from git import GitCommandError, InvalidGitRepositoryError, Repo
from loguru import logger


# ── Clone / Pull ──────────────────────────────────────────────────────────────

def _inject_token(url: str, token: str) -> str:
    """Inject a personal access token into the clone URL."""
    parsed = urlparse(url)
    netloc = f"oauth2:{token}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


async def clone_or_pull(
    repo_url: str,
    branch: str = "main",
    workspace_root: str | None = None,
    token: str | None = None,
) -> str:
    """Clone (or pull) a git repository into a temp workspace directory.

    Returns the path to the local working copy.
    """
    if workspace_root is None:
        workspace_root = tempfile.mkdtemp(prefix="codeguardian_")

    clone_url = _inject_token(repo_url, token) if token else repo_url

    # Derive a stable local path from the repo URL
    repo_name = Path(urlparse(repo_url).path).stem
    local_path = os.path.join(workspace_root, repo_name)

    try:
        if os.path.exists(local_path):
            repo = Repo(local_path)
            origin = repo.remotes.origin
            origin.fetch()
            repo.git.checkout(branch)
            repo.git.pull("origin", branch)
            logger.info(f"Pulled latest {branch!r} into {local_path!r}")
        else:
            repo = Repo.clone_from(clone_url, local_path, branch=branch, depth=50)
            logger.info(f"Cloned {repo_url!r} into {local_path!r}")
    except GitCommandError as exc:
        logger.error(f"Git operation failed: {exc}")
        raise RuntimeError(f"Failed to clone/pull repository: {exc}") from exc

    return local_path


# ── Diff extraction ───────────────────────────────────────────────────────────

def get_diff(repo_path: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> str:
    """Return unified diff text between two refs."""
    try:
        repo = Repo(repo_path)
        diff = repo.git.diff(base_ref, head_ref, unified=3)
        return diff
    except (GitCommandError, InvalidGitRepositoryError) as exc:
        logger.warning(f"Could not get diff: {exc}")
        return ""


def get_changed_files(repo_path: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> list[str]:
    """Return list of changed file paths between two refs."""
    try:
        repo = Repo(repo_path)
        output = repo.git.diff("--name-only", base_ref, head_ref)
        return [f.strip() for f in output.splitlines() if f.strip()]
    except (GitCommandError, InvalidGitRepositoryError):
        return []


# ── PR / MR inline comment writing ───────────────────────────────────────────

async def write_github_pr_comments(
    token: str,
    repo_full_name: str,
    pr_number: int,
    comments: list[dict],
    commit_sha: str | None = None,
) -> None:
    """Post inline review comments on a GitHub pull request.

    Each comment dict: {file_path, line, body}
    """
    try:
        from github import Github, GithubException
    except ImportError:
        logger.warning("PyGithub not installed — cannot write PR comments")
        return

    try:
        g = Github(token)
        repo = g.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        sha = commit_sha or pr.head.sha

        for comment in comments:
            try:
                pr.create_review_comment(
                    body=comment["body"],
                    commit=repo.get_commit(sha),
                    path=comment["file_path"],
                    line=comment["line"],
                )
            except GithubException as exc:
                logger.warning(f"Failed to post GitHub comment: {exc}")
    except Exception as exc:
        logger.error(f"GitHub comment write error: {exc}")


async def write_gitlab_mr_comments(
    token: str,
    project_id: int | str,
    mr_iid: int,
    comments: list[dict],
    commit_sha: str | None = None,
) -> None:
    """Post inline review comments on a GitLab merge request."""
    try:
        import gitlab
    except ImportError:
        logger.warning("python-gitlab not installed — cannot write MR comments")
        return

    try:
        gl = gitlab.Gitlab(url="https://gitlab.com", private_token=token)
        project = gl.projects.get(project_id)
        mr = project.mergerequests.get(mr_iid)

        for comment in comments:
            try:
                mr.discussions.create(
                    {
                        "body": comment["body"],
                        "position": {
                            "base_sha": mr.diff_refs["base_sha"],
                            "head_sha": commit_sha or mr.diff_refs["head_sha"],
                            "start_sha": mr.diff_refs["start_sha"],
                            "position_type": "text",
                            "new_path": comment["file_path"],
                            "new_line": comment["line"],
                        },
                    }
                )
            except Exception as exc:
                logger.warning(f"Failed to post GitLab comment: {exc}")
    except Exception as exc:
        logger.error(f"GitLab comment write error: {exc}")
