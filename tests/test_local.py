import lektorium.repo


def test_create_site(tmpdir):
    repo = lektorium.repo.LocalRepo(tmpdir)
    assert not len(list(repo.root_dir.iterdir()))
    assert not len(list(repo.sites))
    repo.create_site('bow', 'Buy Our Widgets')
    assert len(list(repo.sites)) == 1
    repo = lektorium.repo.LocalRepo(tmpdir)
    assert len(list(repo.sites)) == 1
