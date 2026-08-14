import os
import stat

import pytest

pytest.importorskip("yaml")

from pytumblr.credentials import load_credentials, save_credentials


def test_credentials_are_atomically_saved_owner_only(tmpdir):
    path = str(tmpdir.join("credentials.yml"))
    credentials = {"client_id": "id", "token": {"access_token": "secret"}}
    save_credentials(path, credentials)
    assert load_credentials(path) == credentials
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_credentials_reject_symbolic_links(tmpdir):
    target = str(tmpdir.join("target.yml"))
    link = str(tmpdir.join("credentials.yml"))
    save_credentials(target, {"token": "secret"})
    try:
        os.symlink(target, link)
    except (AttributeError, NotImplementedError, OSError):
        pytest.skip("symbolic links are not available")
    with pytest.raises((ValueError, OSError)):
        load_credentials(link)
