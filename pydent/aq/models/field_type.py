from pydent import aq


class FieldTypeRecord(aq.Record):

    def __init__(self,model,data):
        super(FieldTypeRecord,self).__init__(model,data)
        self.has_many("allowable_field_types", aq.AllowableFieldType)
        self.has_one("operation_type", aq.OperationType, opts={"reference": "parent_id"})
        self.has_one("sample_type", aq.SampleType, opts={"reference": "parent_id"})

    @property
    def is_parameter(self):
        return self.ftype != "sample"

class FieldTypeModel(aq.Base):

    def __init__(self):
        super(FieldTypeModel,self).__init__("FieldType")

FieldType = FieldTypeModel()
