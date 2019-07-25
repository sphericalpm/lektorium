from git import Repo
from git.exc import GitCommandError
from typing import Iterable
import logging

# ==============================================================
# create logger with 'legit'
log = logging.getLogger("legit")
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("legit.log")
fh.setLevel(logging.DEBUG)
# create console handler which logs info messages
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(asctime)s\t%(levelname)s -- %(processName)s %(filename)s:%(lineno)s -- %(message)s"
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)
log.addHandler(fh)
# ==============================================================


class Repository(object):

    def __init__(self, path: str) -> None:
        self.repo = Repo.init(path)

    @classmethod
    def clone(cls, url: str, path: str) -> str:
        log.debug("Clone path", path)
        try:
            Repo.clone_from(url, path)
        except GitCommandError:
            log.error("GitCommandError: no path")
            return None
        return cls(path)

    @classmethod
    def init(cls, path: str) -> str:
        log.debug("init path", path)
        try:
            Repo.init(path)
        except GitCommandError:
            log.error("GitCommandError: no init")
            return None
        return cls(path)

    def create_branch(self, branch_name: str) -> None:
        log.debug("git create branch ", branch_name)
        try:
            self.repo.git.checkout('-b', branch_name)
        except GitCommandError:
            log.error("GitCommandError git checkout ", branch_name)
            self.repo.git.checkout(branch_name)

    def commit(self, message: str) -> None:
        log.debug("git commit ", message)
        self.repo.index.commit(message)

    def add_changes(self, files: Iterable[str] = None) -> None:
        if files:
            for file in files:
                log.info("git add_changes", file)
                self.repo.index.add(file)
        else:
            self.repo.git.add(A=True)

    def push_to_origin(self, branch_name: str) -> None:
        self.repo.head.reset(index=True, working_tree=True)
        self.repo.git.pull("origin", branch_name)
        log.debug("git pull_to_origin")
        self.repo.git.push("origin", 'HEAD:' + branch_name)
        log.debug("git push_to_origin")

    def merge_branch(self, merge_from: str, merge_into: str, merge_commit_message: str) -> None:
        branch_from = self.repo.branches[merge_from]
        branch_into = self.repo.branches[merge_into]
        merge_base = self.repo.merge_base(merge_from, branch_into)
        self.repo.index.merge_tree(branch_into, base=merge_base)
        self.commit(merge_commit_message)
        log.debug("merge from", merge_from, "merge_commit_message ", merge_commit_message)
        branch_from.checkout(force=True)
