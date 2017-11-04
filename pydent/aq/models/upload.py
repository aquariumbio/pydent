"""Upload"""

import aq
import requests


class UploadRecord(aq.Record):

    """UploadRecord is associated with an object in an S3 bucket and is normally
    associated with a data association
    """

    def __init__(self, model, data):
        """Create a new upload object"""
        super(UploadRecord, self).__init__(model, data)

    @property
    def temp_url(self):
        """Returns a temporary S3 url that is valid for a few seconds"""
        return aq.Upload.where({"id": self.id}, {"methods": ["url"]})[0].url

    @property
    def data(self):
        """Fetch content from S3"""
        r = requests.get(self.temp_url)
        return r.content


class UploadModel(aq.Base):

    """UploadModel class, generates UploadRecords"""

    def __init__(self):
        """Make a new UploadModel"""
        super(UploadModel, self).__init__("Upload")


Upload = UploadModel()
