"""AllowableFieldTypes"""

import aq

class AllowableFieldTypeRecord(aq.Record):

    """AllowableFieldTypeRecord used for list of sample types and object types
    that can be associated with a field value.
    """

    def __init__(self, model, data):
        """Make a new AllowableFieldTypeRecord"""
        super(AllowableFieldTypeRecord, self).__init__(model, data)
        self.has_one("field_type", aq.FieldType)
        self.has_one("object_type", aq.ObjectType)
        self.has_one("sample_type", aq.SampleType)

class AllowableFieldTypeModel(aq.Base):

    """AllowableFieldTypeModel class, generates AllowableFieldTypeRecords"""

    def __init__(self):
        """Make a new AllowableFieldTypeModel"""
        super(AllowableFieldTypeModel, self).__init__("AllowableFieldType")

AllowableFieldType = AllowableFieldTypeModel()
