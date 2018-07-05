from pydent.models import Upload
import os
import pytest
import requests

pytestmark = pytest.mark.skip("These tests utilize a live session with alot of requests."
                              "In the future, we may want to utilize something like pyvrc to avoid"
                              "sending live requests to Aquarium.")

def test_upload_file(session):
    aqhttp = session._AqSession__aqhttp

    filename = '25368_A03.fcs'
    files = {
        'file': open(os.path.join('temp', filename), 'rb')
    }

    request = aqhttp.post("krill/upload?job={}".format(115692), files=files)
    u = Upload.load(request)

    dummy_item = session.Sample.find_by_name("DummyPlasmid").items[0]
    da = dummy_item.associate('my file upload', 'my value', upload=u)

    print(da)
    # url = 'http://httpbin.org/post'
    # requests.post(url, files=files)


def test_create_upload(session):

    filename = '25368_A03.fcs'

    dummy_item = session.Sample.find_by_name("DummyPlasmid").items[0]

    da = dummy_item.associate_file_from_path('my upload from path', '', os.path.join('temp', filename))
    print(da)