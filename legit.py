from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from typing import Iterable
# import logging

# parent_commits: Tuple[str, str] = (), author: Tuple[str, str] = author,
# committer: Tuple[str, str] = committer
# author = Actor("An author", "katridi@yandex.ru")
# committer = Actor("A committer", "katridi@yandex.ru")
# TODO Consider author and commiter param
# debug and rewrite clone method and others, add logging


class Repository:

    def __init__(self, path: str) -> None:
        self.repo = Repo.init(path)

    @classmethod
    def clone(cls, url: str, path: str) -> str:
        try:
            Repo(path)
        except InvalidGitRepositoryError:
            Repo.clone_from(url, path)
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

    def merge_branch(self, merge_from: str, merge_into: str, message_for_merging: str) -> None:
        branch_from = self.repo.branches[merge_from]
        branch_into = self.repo.branches[merge_into]
        merge_base = self.repo.merge_base(merge_from, branch_into)
        self.repo.index.merge_tree(branch_into, base=merge_base)
        self.commit(message_for_merging)
        branch_from.checkout(force=True)
