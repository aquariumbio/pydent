"""Job"""

import aq
import json

class JobRecord(aq.Record):

    """JobRecord used to define job implementing an operation"""

    def __init__(self, model, data):
        """Make a new JobRecord"""
        super(JobRecord, self).__init__(model, data)
        self.has_many("operations",
                      aq.Operation,
                      opts={"through": aq.JobAssociation, "association": "operation"})

    def to_json(self, include=[], exclude=[]):
        """Override wild type to_json to convert state string to a hash"""
        j = super(JobRecord, self).to_json(include=include, exclude=exclude)
        if "state" in j:
            j["state"] = json.loads(self.state)
        return j

class JobModel(aq.Base):

    """JobModel class, generates JobRecords"""

    def __init__(self):
        """Make a new JobModel"""
        super(JobModel, self).__init__("Job")

Job = JobModel()
