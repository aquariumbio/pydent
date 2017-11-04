"""Data Associations"""

import aq
import json

class DataAssociationRecord(aq.Record):

    """DataAssociationRecord used to associate data and uploads with plans,
    operations, and items
    """

    def __init__(self, model, data):
        """Make a new DataAssociationRecord"""
        super(DataAssociationRecord, self).__init__(model, data)
        self.has_one("upload", aq.Upload)

    @property
    def value(self):
        """Return the value of a data association"""
        obj = json.loads(self.object)
        if self.key in obj:
            return obj[self.key]
        else:
            return None

    def to_json(self):
        """Overide the wild type to_json method so that the 'object' attribute is
        converted from a string into a hash.
        """
        j = super(DataAssociationRecord, self).to_json()
        j["object"] = {self.key: self.value}
        if "url" in j:
            del j["url"]
        return j

class DataAssociationModel(aq.Base):

    """DataAssociationModel class, generates DataAssociationRecords"""

    def __init__(self):
        """Make a new DataAssociationModel"""
        super(DataAssociationModel, self).__init__("DataAssociation")

DataAssociation = DataAssociationModel()
