"""Wire"""

import aq


class WireRecord(aq.Record):

    """WireRecord associates two field values, defining how operations in a
    plan string together
    """

    def __init__(self, model, data):
        """Make a new WireRecord"""
        super(WireRecord, self).__init__(model, data)
        # Note that 'from' is a Python keyword, so we'll use 'source' instead
        # and then also use 'destinatation', since that sounds good with 'source'
        self.has_one("source", aq.FieldValue, opts={"reference": "from_id"})
        self.has_one("destination", aq.FieldValue, opts={"reference": "to_id"})

    def show(self, pre=""):
        """Show the wire nicely"""
        print(pre + self.source.operation.operation_type.name +
              ":" + self.source.name +
              " --> " + self.destination.operation.operation_type.name +
              ":" + self.destination.name)

    def to_json(self, include=[], exclude=[]):
        """Convert to json, renaming source and destination to from and to"""
        j = super(WireRecord, self).to_json(include=include, exclude=exclude)
        if "source" in j:
            j["from"] = j["source"]
            del j["source"]
        if "destination" in j:
            j["to"] = j["destination"]
            del j["destination"]
        return j


class WireModel(aq.Base):

    """WireModel class, generates WireRecord"""

    def __init__(self):
        """Make a new WireModel"""
        super(WireModel, self).__init__("Wire")


Wire = WireModel()
