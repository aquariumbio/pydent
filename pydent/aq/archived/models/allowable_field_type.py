from pydent import aq


class AllowableFieldTypeRecord(aq.Record):
    def __init__(self, model, data):
        super(AllowableFieldTypeRecord, self).__init__(model, data)
        self.has_one("field_type", aq.FieldType)
        self.has_one("object_type", aq.ObjectType)
        self.has_one("sample_type", aq.SampleType)


class AllowableFieldTypeModel(aq.Base):

    def __init__(self):
        super(AllowableFieldTypeModel, self).__init__("AllowableFieldType")


AllowableFieldType = AllowableFieldTypeModel()
