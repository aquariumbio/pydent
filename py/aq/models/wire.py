import aq

class WireRecord(aq.Record):
    def __init__(self,model,data):
        super(WireRecord,self).__init__(model,data)

class WireModel(aq.Base):

    def __init__(self):
        super(WireModel,self).__init__("Wire")

Wire = WireModel()
