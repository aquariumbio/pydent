import aq

class UploadRecord(aq.Record):
    def __init__(self,model,data):
        super(UploadRecord,self).__init__(model,data)

class UploadModel(aq.Base):

    def __init__(self):
        super(UploadModel,self).__init__("Upload")

Upload = UploadModel()
