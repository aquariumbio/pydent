import aq

class WireRecord(aq.Record):

    def __init__(self,model,data):
        super(WireRecord,self).__init__(model,data)
        # Note that 'from' is a Python keyword, so we'll use 'source' instead
        # and then also use 'destinatation', since that sounds good with 'source'
        self.has_one("source", aq.FieldValue, opts={"reference": "from_id"})
        self.has_one("destination", aq.FieldValue, opts={"reference": "to_id"})

class WireModel(aq.Base):

    def __init__(self):
        super(WireModel,self).__init__("Wire")

Wire = WireModel()
