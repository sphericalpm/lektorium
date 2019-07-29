from git import Repo
from git.exc import GitCommandError
from typing import Iterable
import logging

log = logging.getLogger("legit")
log.setLevel(logging.DEBUG)
fh = logging.FileHandler("legit.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s\t%(levelname)s -- %(processName)s %(filename)s:%(lineno)s -- %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)
log.addHandler(ch)
log.addHandler(fh)


class Repository(object):

    def __init__(self, path: str) -> None:
        log.debug(f"git init {path}")
        self.repo = Repo.init(path)

    @classmethod
    def clone(cls, url: str, path: str) -> str:
        """Git function which provides interface to clone from remote to local machine.
        
        Note:
            Git accordance is "git clone `url` `path`"
        
        Args:
            url: The url of remote (Github, Gitlab, etc)
            path: The path to locate remote repo in the local machine.
        
        Returns:
            The return value is path to repo. Str for success, None otherwise.
        
        Examples:
            >>> path_to_repo = Repository.clone(url, path).repo
        
        """
        log.debug(f"git clone {url} {path}")
        try:
            Repo.clone_from(url, path)
        except GitCommandError:
            log.error(f"GitCommandError: {GitCommandError}, no path {path}")
            return None
        return cls(path)

    @classmethod
    def init(cls, path: str) -> str:
        """Git function which provides interface to initialize repository as git repository.
        
        Note:
            Git accordance is "git init `path`"
        
        Args:
            path: The path to initialize repo as git repository.
        
        Returns:
            The return value is path to repo. Str for success, None otherwise.
        
        Examples:
            >>> path_to_repo = Repository.init(path).repo
        
        """
        log.debug(f"git init {path}")
        try:
            Repo.init(path)
        except GitCommandError:
            log.error(f"GitCommandError: {GitCommandError}")
            return None
        return cls(path)

    def create_branch(self, branch_name: str) -> None:
        """Git function which provides interface to create a new branch 
        or to switch between them.
        
        Note:
            Git accordance is "git checkout -b `branch_name`"
        
        Args:
            branch_name: The name for branch you want to create/switch.
        
        Examples:
            >>> path_to_repo = Repository.init(path).repo
            >>> path_to_repo.create_branch(`branch_name`)
        
        """
        log.debug(f"git checkout -b {branch_name}")
        try:
            self.repo.git.checkout('-b', branch_name)
        except GitCommandError:
            log.error(f"GitCommandError git checkout {branch_name}")
            self.repo.git.checkout(branch_name)

    def commit(self, message: str) -> None:
        """Git function which provides interface to commit changes.
        
        Note:
            Git accordance is "git commit -m `message`"
        
        Args:
            branch_name: The name for branch you want to create/switch.
        
        Examples:
            >>> path_to_repo.commit(`message`)
        
        """
        log.debug(f"git commit -m \"{message}\"")
        self.repo.index.commit(message)
        
    def add_changes(self, files: Iterable[str] = None) -> None:
        """Git function which provides interface to commit changes.
        
        Note:
            Git accordance is "git add `files`" or "git add ."
        
        Args:
            files: The path to files to add or None if one wants to add them all
        
        Examples:
            >>> path_to_repo.add(`files`)
            >>> path_to_repo.add()
        
        """
        if files:
            for file in files:
                log.debug(f"git add {file}")
                self.repo.index.add(file)
        else:
            log.debug(f"git add .")
            self.repo.git.add(A=True)

    def push_to_origin(self, branch_name: str) -> None:
        self.repo.head.reset(index=True, working_tree=True)
        log.debug(f"git pull origin {branch_name}")
        self.repo.git.pull("origin", branch_name)
        log.debug(f"git push to origin, HEAD: {branch_name}")
        self.repo.git.push(f"git push origin \'HEAD:\' {branch_name}")

    def merge_branch(self, merge_from: str, merge_into: str, merge_commit_message: str) -> None:
        branch_from = self.repo.branches[merge_from]
        branch_into = self.repo.branches[merge_into]
        merge_base = self.repo.merge_base(merge_from, branch_into)
        self.repo.index.merge_tree(branch_into, base=merge_base)
        self.commit(merge_commit_message)
        log.debug(f"merge from {merge_from} into {merge_into} merge commit message: {merge_commit_message}")
        branch_from.checkout(force=True)
