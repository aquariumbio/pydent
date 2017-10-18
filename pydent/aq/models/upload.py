from pydent import aq
import requests

class UploadRecord(aq.Record):

    def __init__(self,model,data):
        super(UploadRecord,self).__init__(model,data)

    @property
    def temp_url(self):
        """Returns a temporary S3 url that is valid for a few seconds"""
        return aq.Upload.where({"id": self.id},{"methods": ["url"]})[0].url

    @property
    def data(self):
        r = requests.get(self.temp_url)
        return r.content

class UploadModel(aq.Base):

    def __init__(self):
        super(UploadModel,self).__init__("Upload")

Upload = UploadModel()
