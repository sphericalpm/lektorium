import git
from git import Repo

def clone_repo(url, path):
    return Repo.clone_from(url, path, branch='master')
 
def create_branch(repo, branch_name):
    repo.git.checkout('HEAD', b=branch_name)
 
def commit(repo, meaningful_msg):
    repo.index.commit(meaningful_msg)
 
def add_changes(repo, files=[]):
    [repo.index.add(file) for file in files] or repo.git.add(A=True)
 
def push_to_origin(repo, branch_name):
    print(repo.untracked_files)
    repo.head.reset(index=True, working_tree=True)
    repo.git.pull("origin", branch_name)    
    repo.git.push("origin", 'HEAD:' + branch_name)
