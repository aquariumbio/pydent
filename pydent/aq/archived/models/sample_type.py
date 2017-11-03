from pydent import aq


class SampleTypeRecord(aq.Record):
    def __init__(self, model, data):
        super(SampleTypeRecord, self).__init__(model, data)
        self.has_many("samples", aq.Sample)
        self.has_many_generic("field_types", aq.FieldType)


class SampleTypeModel(aq.Base):

    def __init__(self):
        super(SampleTypeModel, self).__init__("SampleType")


SampleType = SampleTypeModel()
