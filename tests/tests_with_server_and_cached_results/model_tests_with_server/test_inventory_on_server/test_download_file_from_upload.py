import time
from os.path import isfile
from os.path import join
from uuid import uuid4

import pytest


@pytest.mark.recode("no")
def test_download(session, tmpdir):
    """Expect a new file to be created from the 'download' method."""
    upload = session.Upload.one()

    path = tmpdir.mkdir("trident_test_downloads")
    newfile = upload.download(path)

    assert isfile(newfile)


@pytest.fixture
def example_item(session):
    return session.Item.one()


@pytest.mark.recode("no")
def test_upload(session, tmpdir, example_item):
    # upload a new file
    path = tmpdir.mkdir("trident_test_uploads")
    filepath = join(path, "test_upload.txt")
    val = str(uuid4())
    with open(filepath, "w") as f:
        f.write(val)

    # download the recently uploaded file
    da = example_item.associate_file_from_path("test_upload", val, filepath)
    download_path = tmpdir.mkdir("test_download_from_server")
    time.sleep(1.0)
    assert da.upload
    fp = da.upload.download(download_path)

    # verify file contents
    with open(fp, "r") as f:
        assert val in f.read()
