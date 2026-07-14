"""LangChain @tool for extracting git diff."""

from langchain_core.tools import tool

from app.git.service import get_diff


@tool
def get_git_diff(repo_path: str, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> str:
    """Get unified diff between two git refs.

    Args:
        repo_path: Absolute path to the local git repository.
        base_ref: Base git ref (commit SHA, branch, or HEAD~N). Default: HEAD~1.
        head_ref: Head git ref. Default: HEAD.

    Returns:
        Unified diff text (empty string if no diff or error).
    """
    return get_diff(repo_path, base_ref, head_ref)
