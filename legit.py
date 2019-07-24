from git import Repo
from git.exc import GitCommandError
from typing import Iterable


class Repository:

    def __init__(self, path: str) -> None:
        self.repo = Repo.init(path)

    @classmethod
    def clone(cls, url: str, path: str) -> str:
        try:
            Repo.clone_from(url, path)
        except GitCommandError:
            return None
        return cls(path)

    @classmethod
    def init(cls, path: str) -> str:
        try:
            Repo.init(path)
        except GitCommandError:
            return None
        return cls(path)

    def create_branch(self, branch_name: str) -> None:
        try:
            self.repo.git.checkout('-b', branch_name)
        except GitCommandError:
            self.repo.git.checkout(branch_name)

    def commit(self, message: str) -> None:
        self.repo.index.commit(message)

    def add_changes(self, files: Iterable[str] = None) -> None:
        if files:
            for file in files:
                self.repo.index.add(file)
        else:
            self.repo.git.add(A=True)

    def push_to_origin(self, branch_name: str) -> None:
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.git.pull("origin", branch_name)
        self.repo.git.push("origin", 'HEAD:' + branch_name)

    def merge_branch(self, merge_from: str, merge_into: str, merge_commit_message: str) -> None:
        branch_from = self.repo.branches[merge_from]
        branch_into = self.repo.branches[merge_into]
        merge_base = self.repo.merge_base(merge_from, branch_into)
        self.repo.index.merge_tree(branch_into, base=merge_base)
        self.commit(merge_commit_message)
        branch_from.checkout(force=True)
