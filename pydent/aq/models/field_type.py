"""Field Type"""

import aq

class FieldTypeRecord(aq.Record):

    """FieldTypeRecord is used to define the input and output types of operation
    types, and also the types of associations allowed for sample types.
    """

    def __init__(self, model, data):
        """Make a new FieldTypeRecord"""
        super(FieldTypeRecord, self).__init__(model, data)
        self.has_many("allowable_field_types", aq.AllowableFieldType)
        self.has_one("operation_type", aq.OperationType,
                     opts={"reference": "parent_id"})
        self.has_one("sample_type", aq.SampleType,
                     opts={"reference": "parent_id"})

    @property
    def is_parameter(self):
        """Return true if the field type is a parameter and not a sample"""
        return self.ftype != "sample"


class FieldTypeModel(aq.Base):

    """FieldTypeModel class, generates FieldValueRecords"""

    def __init__(self):
        """Make a new FieldTypeModel"""
        super(FieldTypeModel, self).__init__("FieldType")


FieldType = FieldTypeModel()
