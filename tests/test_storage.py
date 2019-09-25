import tempfile
import shutil
from lektorium.repo.local.objects import Site
from lektorium.repo.local import FileStorage, LocalLektor


def test_everything(tmpdir):
    storage = FileStorage(tmpdir)
    assert isinstance(storage.config, dict)
    site_id = 'site-id'
    path = storage.create_site(
        LocalLektor,
        'Site Name',
        'Site Owner',
        site_id,
    )
    assert path.exists()
    storage.site_config(site_id).get('project.name')
    storage.config[site_id] = Site(site_id, None)
    storage = FileStorage(tmpdir)
    assert len(storage.config)
    session_dir = tmpdir / 'session-id'
    assert not session_dir.exists()
    storage.create_session(site_id, 'session-id', session_dir)
    assert len(session_dir.listdir())
    if (tmpdir / site_id).exists():
        shutil.rmtree(tmpdir / site_id)
        storage.site_config(site_id).get('project.name')
