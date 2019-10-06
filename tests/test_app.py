from unittest.mock import MagicMock, patch
from lektorium import app


def test_app():
    with patch('lektorium.repo.LocalRepo') as LocalRepo:
        app.create_app(app.RepoType.LOCAL, '', '')
        LocalRepo.assert_called_once()
        (storage, *_), kwargs = LocalRepo.call_args
        assert not kwargs
        assert hasattr(storage, 'config')
