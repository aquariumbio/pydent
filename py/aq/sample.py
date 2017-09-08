import aq

class SampleRecord(aq.Record):

    def __init__(self,model,data):
        super(SampleRecord,self).__init__(model,data)
        self.has_one("sample_type", aq.SampleType)

class SampleModel(aq.Base):

    def __init__(self):
        super(SampleModel,self).__init__("Sample")

Sample = SampleModel()
