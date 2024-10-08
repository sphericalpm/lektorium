from unittest.mock import patch

import pytest

from lektorium import app


def test_app():
    with patch('lektorium.repo.LocalRepo') as local_repo:
        app.create_app(app.RepoType.LOCAL, '', '')
        local_repo.assert_called_once()
        (storage, *_), kwargs = local_repo.call_args
        assert kwargs == dict(sessions_root=None)
        assert hasattr(storage, 'config')


@pytest.mark.skip(reason='breaks many other tests')
async def test_index(aiohttp_client, loop):
    client = await aiohttp_client(app.create_app(auth='test.auth0.com'))
    assert (await client.get('/')).status == 200
    assert (await client.get('/scripts/main.js')).status == 200
    assert (await client.get('/components/App.vue')).status == 200
    response = await client.get('/auth0-config')
    assert response.status == 200
    assert 'lektoriumAuth0Config' in await response.text()
    assert 'test.auth0.com' in await response.text()
