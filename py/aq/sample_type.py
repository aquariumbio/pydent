import aq

class SampleTypeRecord(aq.Record):
    pass

class SampleTypeModel(aq.Base):

    def __init__(self):
        super(SampleTypeModel,self).__init__("SampleType")

SampleType = SampleTypeModel()
