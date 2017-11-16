import pytest
from pydent.models import User
from pydent.base import ModelBase, ModelRegistry
from pydent.marshaller import add_schema
from marshmallow import fields


def test_login(session, config):
    """Test actually logging into the Aquarium server detailed in the config."""
    current = session.current_user
    assert isinstance(current, User)
    assert current.login == config["login"]
    print(current)


def test_base_registery():
    """All models that are subclasses of the Base class get collected into a BaseRegistry."""

    @add_schema
    class MyModel(ModelBase):
        class Fields:
            field4 = fields.Field()
            field5 = fields.Field()
            something = 5
            additional = ("field1", "field2")
            include = {
                "field3": fields.Field(),
                "field6": fields.Field()
            }

        def __init__(self):
            pass

    assert MyModel.__name__ in ModelRegistry.models
    assert MyModel == ModelRegistry.get_model("MyModel")


def test_load_dump_repeat(session):
    job = session.Job.find(1111)
    job.dump()
    print(job.dump())
    job2 = session.Job.find(1111)


def test_with_sample_type(session):

    st = session.SampleType.find(1)
    samples = st.samples
    print(samples)
    st.dump()

def test_plan(session):
    plan = session.Plan.find(5198)
    print(plan.data_associations)
    print(plan.plan_associations)
    print(plan.operations)

    # jobs = plan.operations[0].jobs
    # print(jobs)
    #
    # plan.dump()
    # print(plan.dump())
    #
    # # print(plan.dump(additional=("plan_associations")))
    # d = plan.model_schema(additional=("plan_associations",)).dump(plan)

    pa = session.PlanAssociation.find(7116)
    print(pa)
    pa.dump()

def test_wire(session):
    w = session.Wire.find(10)
    print(w.dump())


def test_code(session):
    c = session.OperationType.find_by_name("Protocol1")
    code = c.code
    code.content = "New content"
    code.update()