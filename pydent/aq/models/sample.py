"""Sample"""

import aq


class SampleRecord(aq.Record):

    """SampleRecord defines a particular sample"""

    def __init__(self, model, data):
        """Make a new SampleRecord"""
        super(SampleRecord, self).__init__(model, data)
        self.has_one("sample_type", aq.SampleType)
        self.has_many("items", aq.Item)
        self.has_many_generic("field_values", aq.FieldValue)

    @property
    def identifier(self):
        """Return the identifier used by Aquarium in autocompletes"""
        return str(self.id) + ": " + self.name

    def field_value(self, name):
        """Return the field value names 'name'"""
        for field_value in self.field_values:
            if field_value.name == name:
                return field_value
        return None


class SampleModel(aq.Base):

    """SampleModel class, generates SampleRecords"""

    def __init__(self):
        """Make a new SampleModel"""
        super(SampleModel, self).__init__("Sample")

    def create(self, samples):
        """Create new samples in the Aquarium database"""
        json = [s.to_json() for s in samples]
        result = aq.http.post('/browser/create_samples', {"samples": json})
        if "errors" in result:
            raise Exception(", ".join(result["errors"]))
        else:
            return [aq.Sample.record(s) for s in result["samples"]]


Sample = SampleModel()
