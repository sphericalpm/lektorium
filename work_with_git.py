import git
from git import Repo
from git import Actor


author = Actor("An author", "katridi@yandex.ru")
committer = Actor("A committer", "katridi@yandex.ru")

def clone_repo(url, path):
    try:
        return Repo(path) #repo already exists
    except git.exc.InvalidGitRepositoryError:
        return Repo.clone_from(url, path, branch='master') #clone from remote

def create_branch(repo, branch_name):
    try:
        repo.git.checkout('-b', branch_name) #branch exists
    except git.exc.GitCommandError:
        repo.git.checkout(branch_name) #create new
         
def commit(repo, meaningful_msg, parent_commits=(), author=author, committer=committer):
    repo.index.commit(meaningful_msg)
 
def add_changes(repo, files=[]):
    [repo.index.add(file) for file in files] or repo.git.add(A=True)
    
def merge_branch(repo, branch_name, msg_for_merging, parent_branch='master'):
    current = repo.branches[branch_name]
    master = repo.branches[parent_branch]
    merge_base = repo.merge_base(branch_name, master)
    repo.index.merge_tree(master, base=merge_base)
    commit(repo, msg_for_merging, parent_commits=(current.commit, master.commit)) 
    #At this point, we have successfully merged the two branches but we have not modified the working directory.
    current.checkout(force=True) #We need to perform a checkout of the new commit
 
def push_to_origin(repo, branch_name):
    print(repo.untracked_files)
    repo.head.reset(index=True, working_tree=True)
    repo.git.pull("origin", branch_name)    
    repo.git.push("origin", 'HEAD:' + branch_name)
