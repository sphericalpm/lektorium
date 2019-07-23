from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from typing import List, Iterable, Tuple

# parent_commits: Tuple[str, str] = (), author: Tuple[str, str] = author, committer: Tuple[str, str] = committer
#TODO Consider author and commiter param
# author = Actor("An author", "katridi@yandex.ru")
# committer = Actor("A committer", "katridi@yandex.ru")


class Repository:

    def __init__(self, path) -> None:
        self.repo = Repo.init(path)

    @classmethod
    def clone(cls, url: str, path: str) -> str:
        try:
            Repo(path)
        except InvalidGitRepositoryError:
            Repo.clone_from(url, path)
        return cls(path)

    def create_branch(self, branch_name: str) -> None:
        # Check if branch exist in other case create new branch
        try:
            self.repo.git.checkout('-b', branch_name)
        except GitCommandError:
            self.repo.git.checkout(branch_name)

    def commit(self, meaningful_msg: str) -> None:
        self.repo.index.commit(meaningful_msg)

    def add_changes(self, files: Iterable[str] = ()) -> None:
        [self.repo.index.add(file) for file in files] or self.repo.git.add(A=True)

    def push_to_origin(self, branch_name: str) -> None:
        print(self.repo.untracked_files)
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.git.pull("origin", branch_name)
        self.repo.git.push("origin", 'HEAD:' + branch_name)

    def merge_branch(self, branch_name: str, msg_for_merging: str, parent_branch: str = 'master') -> None:
        current = self.repo.branches[branch_name]
        master = self.repo.branches[parent_branch]
        merge_base = self.repo.merge_base(branch_name, master)
        self.repo.index.merge_tree(master, base=merge_base)
        self.commit(msg_for_merging)
        # At this point, we have successfully merged the two branches
        # but we have not modified the working directory.
        current.checkout(force=True)  # We need to perform a checkout of the new commit
