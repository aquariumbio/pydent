from pydent import aq
import json

class JobRecord(aq.Record):

    def __init__(self,model,data):
        super(JobRecord,self).__init__(model,data)
        self.has_many("operations",
            aq.Operation,
            opts={"through": aq.JobAssociation, "association": "operation"})

    def to_json(self,include=[],exclude=[]):
        j = super(JobRecord,self).to_json(include=include,exclude=exclude)
        if "state" in j:
            j["state"] = json.loads(self.state)
        return j

class JobModel(aq.Base):

    def __init__(self):
        super(JobModel,self).__init__("Job")

Job = JobModel()
