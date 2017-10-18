import py.aq as aq

class SampleRecord(aq.Record):

    def __init__(self,model,data):
        super(SampleRecord,self).__init__(model,data)
        self.has_one("sample_type", aq.SampleType)
        self.has_many("items", aq.Item)
        self.has_many_generic("field_values", aq.FieldValue)

    @property
    def identifier(self):
        return str(self.id) + ": " + self.name

    def field_value(self,name):
        for fv in self.field_values:
            if fv.name == name:
                return fv
        return None

class SampleModel(aq.Base):

    def __init__(self):
        super(SampleModel,self).__init__("Sample")

    def create(self,samples):
        json = [ s.to_json() for s in samples ]
        print(json)
        r = aq.http.post('/browser/create_samples', { "samples": json })
        if "errors" in r:
            raise Exception(", ".join(r["errors"]))
        else:
            return [ aq.Sample.record(s) for s in r["samples"]]

Sample = SampleModel()
