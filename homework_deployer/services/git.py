from typing import Optional

from git import Repo


def clone_repository(repo_url: str, destination: str, commit: Optional[str] = None) -> None:
    """
    Clones a Git repository to the specified destination and optionally checks out a specific commit.

    Args:
        repo_url (str): The URL of the Git repository to clone.
        destination (str): The local path where the repository should be cloned.
        commit (Optional[str]): The commit SHA to check out after cloning. If None, the
            repository is left on the default branch's latest commit.

    Raises:
        git.exc.GitCommandError: If there is an error during cloning.
    """
    try:
        repo = Repo.clone_from(repo_url, destination)
        if commit is not None:
            repo.git.checkout(commit)
    except Exception as e:
        print(f"An error occurred while cloning the repository: {e}")
