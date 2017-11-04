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
        for fv in self.field_values:
            if fv.name == name:
                return fv
        return None


class SampleModel(aq.Base):

    """SampleModel class, generates SampleRecords"""

    def __init__(self):
        """Make a new SampleModel"""
        super(SampleModel, self).__init__("Sample")

    def create(self, samples):
        """Create new samples in the Aquariu database"""
        json = [s.to_json() for s in samples]
        print(json)
        r = aq.http.post('/browser/create_samples', {"samples": json})
        if "errors" in r:
            raise Exception(", ".join(r["errors"]))
        else:
            return [aq.Sample.record(s) for s in r["samples"]]


Sample = SampleModel()
