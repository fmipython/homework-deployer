from git import Repo


def clone_repository(repo_url: str, destination: str) -> None:
    """
    Clones a Git repository to the specified destination.

    Args:
        repo_url (str): The URL of the Git repository to clone.
        destination (str): The local path where the repository should be cloned.

    Raises:
        git.exc.GitCommandError: If there is an error during cloning.
    """
    try:
        Repo.clone_from(repo_url, destination)
    except Exception as e:
        print(f"An error occurred while cloning the repository: {e}")
