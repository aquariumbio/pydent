"""
Models related to jobs, or operation execution.
"""

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import JSON, HasOne, HasMany, HasManyThrough


@add_schema
class Job(ModelBase):
    """A Job model"""

    fields = dict(
        job_associations=HasMany("JobAssociation", "Job"),
        operations=HasManyThrough("Operation", "JobAssociation"),
        state=JSON(),
    )

    @property
    def is_complete(self):
        return self.pc == -2

    @property
    def uploads(self):
        http = self.session._AqSession__aqhttp
        return http.get("krill/uploads?job={}".format(self.id))["uploads"]

    @property
    def start_time(self):
        return self.state[0]["time"]

    @property
    def end_time(self):
        return self.state[-2]["time"]


@add_schema
class JobAssociation(ModelBase):
    """A JobAssociation model"""

    fields = dict(job=HasOne("Job"), operation=HasOne("Operation"))
