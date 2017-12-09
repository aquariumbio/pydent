"""Sample Type"""

import aq


class SampleTypeRecord(aq.Record):

    """SampleTypeRecord defines a type of sample such as a plasmid or primer"""

    def __init__(self, model, data):
        """Make a new SampleTypeRecord"""
        super(SampleTypeRecord, self).__init__(model, data)
        self.has_many("samples", aq.Sample)
        self.has_many_generic("field_types", aq.FieldType)


class SampleTypeModel(aq.Base):

    """SampleTypeModel class, generates SampleTypeRecords"""

    def __init__(self):
        """Make a new SampleTypeModel"""
        super(SampleTypeModel, self).__init__("SampleType")


SampleType = SampleTypeModel()
