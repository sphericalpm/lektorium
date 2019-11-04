from unittest.mock import patch
from lektorium import app


def test_app():
    # this test can be slow on client renew because it install's
    # (and indirectly tests) client code, so it is important to leave
    # this behaviour
    with patch('lektorium.repo.LocalRepo') as LocalRepo:
        app.create_app(app.RepoType.LOCAL, '', '')
        LocalRepo.assert_called_once()
        (storage, *_), kwargs = LocalRepo.call_args
        assert kwargs == dict(sessions_root=None)
        assert hasattr(storage, 'config')
