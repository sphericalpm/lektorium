from flask import g as flask_store
from . import app
from .repo import ListRepo, GitRepo, SITES


# app.repo = GitRepo('gitlab/service')
app.repo = ListRepo(SITES)
app.app.run()
