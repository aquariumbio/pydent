import aq

class DataAssociationRecord(aq.Record):
    def __init__(self,model,data):
        super(DataAssociationRecord,self).__init__(model,data)

class DataAssociationModel(aq.Base):

    def __init__(self):
        super(DataAssociationModel,self).__init__("DataAssociation")

DataAssociation = DataAssociationModel()
