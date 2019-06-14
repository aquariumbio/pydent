
def test_upload_temp_url(session):
    u = session.Upload.one()
    print(u.temp_url())

