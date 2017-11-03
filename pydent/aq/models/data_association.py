import aq
import json

class DataAssociationRecord(aq.Record):

    def __init__(self,model,data):
        super(DataAssociationRecord,self).__init__(model,data)
        self.has_one("upload", aq.Upload)

    @property
    def value(self):
        obj = json.loads(self.object)
        if self.key in obj:
            return obj[self.key]
        else:
            return None

    def to_json(self):
        j = super(DataAssociationRecord,self).to_json()
        j["object"] = { self.key: self.value }
        if "url" in j:
            del j["url"]
        return j

class DataAssociationModel(aq.Base):

    def __init__(self):
        super(DataAssociationModel,self).__init__("DataAssociation")

DataAssociation = DataAssociationModel()
