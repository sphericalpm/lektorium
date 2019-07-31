from typing import Iterable
import logging

from git import Repo
from git.exc import GitCommandError

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
    """GitPython provides object model access to your git repository.
    This class wraps up some fuctions of GitPython

    Attributes:
        repo : This is path to git repository. Most of the GitPython functions
        use it to operate with repository.
        
    """

    def __init__(self, path: str) -> None:
        """This command creates an empty Git repository - basically
        a .git directory with subdirectories for objects,
        refs/heads, refs/tags, and template files.
        An initial HEAD file that references the HEAD
        of the master branch is also created.

        Note:
            Git accordance is "git init `path`"
            https://git-scm.com/docs/git-init

        Args:
            path: Path to the repository you want to be git repository

        """
        log.debug(f"git init {path}")
        try:
            self.repo = Repo.init(path)
        except GitCommandError:
            logging.exception(f"GitCommandError: git init {GitCommandError}, {path} traceback")
        
    @classmethod
    def clone(cls, url: str, path: str) -> str:
        """Git function which provides interface to clone from remote
        to local machine.
        
        Note:
            Git accordance is "git clone `url` `path`"
            https://git-scm.com/docs/git-clone
        
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
            logging.exception(f"GitCommandError: git clone {GitCommandError}, {path} traceback")
            return None
        return cls(path)

    @classmethod
    def init(cls, path: str) -> str:
        """This command creates an empty Git repository - basically
        a .git directory with subdirectories for objects,
        refs/heads, refs/tags, and template files.
        An initial HEAD file that references the HEAD
        of the master branch is also created.
        
        Note:
            Git accordance is "git init `path`"
            https://git-scm.com/docs/git-init
        
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
            logging.exception(f"GitCommandError: git init {GitCommandError} traceback")
            return None
        return cls(path)

    def checkout(self, branch_name: str) -> None:
        """Updates files in the working tree to match
        the version in the index or the specified tree.
        If no paths are given, git checkout will also update HEAD
         to set the specified branch as the current branch.
        
        Note:
            Git accordance is "git checkout -b `branch_name`"
            https://git-scm.com/docs/git-checkout
        
        Args:
            branch_name: The name for branch you want to create/switch.
        
        Examples:
            >>> path_to_repo = Repository.init(path).repo
            >>> path_to_repo.checkout(`branch_name`)
        
        """
        log.debug(f"git checkout -b {branch_name}")
        try:
            self.repo.git.checkout('-b', branch_name)
        except GitCommandError:
            logging.exception(f"GitCommandError: git checkout {branch_name} traceback")
            self.repo.git.checkout(branch_name)

    def commit(self, message: str) -> None:
        """Create a new commit containing the current contents
        of the index and the given log message describing the changes.
        
        Note:
            Git accordance is "git commit -m `message`"
            https://git-scm.com/docs/git-commit
        
        Args:
            branch_name: The name for branch you want to create/switch.
        
        Examples:
            >>> path_to_repo.commit(`message`)
        
        """
        log.debug(f"git commit -m \"{message}\"")
        try:
            self.repo.index.commit(message)
        except GitCommandError:
            logging.exception(f"GitCommandError: git commit {GitCommandError} traceback")
   
    def add_changes(self, files: Iterable[str] = None) -> None:
        """This command updates the index using
        the current content found in the working tree,
         to prepare the content staged for the next commit.
        
        Note:
            Git accordance is "git add `files`" or "git add ."
            https://git-scm.com/docs/git-add
        
        Args:
            files: The path to files to add or None to add all
        
        Examples:
            >>> path_to_repo.add(`files`)
            >>> path_to_repo.add()
        
        """
        try:
            if files:
                for file in files:
                    log.debug(f"git add {file}")
                    self.repo.index.add(file)
            else:
                log.debug(f"git add .")
                self.repo.git.add(A=True)
        except GitCommandError:
            logging.exception(f"GitCommandError: git add {GitCommandError} traceback")
   
    def push_to_origin(self, branch_name: str) -> None:
        """Updates remote refs using local refs, while sending
        objects necessary to complete the given refs.
        
        Note:
            Git accordance is "git pull origin"
            https://git-scm.com/docs/git-push
        
        Args:
            branch_name: The name for branch you want to push.
        
        Examples:
            >>> path_to_repo.push_to_origin(`master`)
        
        """
        self.repo.head.reset(index=True, working_tree=True)
        log.debug(f"git pull origin {branch_name}")
        self.repo.git.pull("origin", branch_name)
        log.debug(f"git push to origin, HEAD: {branch_name}")
        self.repo.git.push(f"git push origin \'HEAD:\' {branch_name}")

    def merge_branch(self, merge_from: str, merge_into: str, merge_commit_message: str) -> None:
        """Incorporates changes from the named commits
        (since the time their histories diverged from the current branch)
        into the current branch.

        Note:
            Git accordance is "git merge `merge_from` `merge_into`"
            https://git-scm.com/docs/git-merge
        
        Args:
            merge_from: The name for branch you want to insert.
            merge_into: The name for branch you want to insert into
            merge_commit_message: The log message from the user describing the changes.
        Examples:
            >>> path_to_repo.merge_branch(`merge_from`, `merge_into`, `merge_commit_message`)
        
        """
        branch_from = self.repo.branches[merge_from]
        branch_into = self.repo.branches[merge_into]
        merge_base = self.repo.merge_base(merge_from, branch_into)
        self.repo.index.merge_tree(branch_into, base=merge_base)
        self.commit(merge_commit_message)
        log.debug(f"merge from {merge_from} into {merge_into} merge commit message: {merge_commit_message}")
        branch_from.checkout(force=True)
