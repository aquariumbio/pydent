class TestUpload:
    def test_retrieve_upload(self, session):
        upload = session.Upload.find(10502)
        assert upload
        assert upload.size == 3011
        assert upload.name == 'jid_57977_item_120721_03132018_cal_gfp.csv'
        assert upload.job.id == 94686
