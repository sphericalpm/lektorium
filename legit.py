import git
from git import Repo
from git import Actor


author = Actor("An author", "katridi@yandex.ru")
committer = Actor("A committer", "katridi@yandex.ru")


class Repository:

	def __init__(self, path):
		self.repo = Repo.init(path)

	@classmethod
	def clone(cls, url, path):
		try:
			Repo(path)
		except git.exc.InvalidGitRepositoryError:
			Repo.clone_from(url, path, branch='master') #clone from remote
		return cls(path)

	def create_branch(self, branch_name):
		try:
			self.repo.git.checkout('-b', branch_name) #branch exists
		except git.exc.GitCommandError:
			self.repo.git.checkout(branch_name) #create new

	def commit(self, meaningful_msg, parent_commits=(), author=author, committer=committer):
		self.repo.index.commit(meaningful_msg)

	def add_changes(self, files=[]):
		[self.repo.index.add(file) for file in files] or self.repo.git.add(A=True)

	def push_to_origin(self, branch_name):
		print(self.repo.untracked_files)
		self.repo.head.reset(index=True, working_tree=True)
		self.repo.git.pull("origin", branch_name)    
		self.repo.git.push("origin", 'HEAD:' + branch_name)
		
	def merge_branch(self, branch_name, msg_for_merging, parent_branch='master'):
		current = self.repo.branches[branch_name]
		master = self.repo.branches[parent_branch]
		merge_base = self.repo.merge_base(branch_name, master)
		self.repo.index.merge_tree(master, base=merge_base)
		self.commit(msg_for_merging, parent_commits=(current.commit, master.commit)) 
		#At this point, we have successfully merged the two branches but we have not modified the working directory.
		current.checkout(force=True) #We need to perform a checkout of the new commit


