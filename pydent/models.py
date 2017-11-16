"""models.py

This module contains a set of classes for various various Aquarium objects. Trident models
inherit the Base class and have a model schema (handled by '@add_schema`) that handles
the JSON loading and dumping.

By default, Trident models capture ALL JSON attribute/values and sets the attributes to the
resultant object.

    e.g.
        u = User.load({"id": 1, "login": "John"})
        u.login    # => "John"
        u.id       # => 1

Fields and field options are added as class variables in the model class definition.
Below lists various field options and their default values.

        load_all = True     # load missing data attributes not explicitly defined during serialization
        strict = True       # throw error during marshalling instead of storing error
        include = {}        # fields to include for serialization/deserialization.
        additional = ()     # explicitly defined fields for serialization/deserialization.
        ignore = ()         # fields to filter during deserialization. These fields will be filtered from the JSON.
        load_only = ()      # fields to ignore during serialization
        dump_only = ()      # fields to ignore during deserialization

Trident models can also have nested relationships (for example, a Sample my possess a single SampleType while
a SampleType may possess several Samples). These relationships can be specified in the class definition along
with the field options above as in:

    @add_schema
    class SampleType(Base):
        samples = fields.Nested("Sample", many=True)

In many cases, the model contains only a reference to the nested relationship, in this case, special fields
One and Many may be used to define this relationship. When called as an attribute, Trident will automatically
use the session connection with Aquarium to retrieve the given model.

For example, the following will define that SampleType has many Samples. When .samples is called on a
SampleType instance, Trident will use the database to retrieve all samples that have a sample_type_id
equal to the id of the SampleType:

    @add_schema
    class SampleType(Base):
        samples = Many("Sample", params={"sample_type_id": lambda self: self.id})
"""

# TODO: Better errors for incorrect models

import json

from marshmallow import fields
from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import One, Many, HasOne, HasMany, HasManyThrough, HasManyGeneric
from pydent.utils import magiclist


##### Mixins #####

class HasCode(object):
    """Access to latest code for OperationType, Library, etc."""

    @property
    def code(self):
        if len(self.codes) > 0:
            return self.codes[-1]


##### Models #####

@add_schema
class Account(ModelBase):
    """An Account model"""


@add_schema
class AllowableFieldType(ModelBase):
    """A AllowableFieldType model"""
    fields = dict(
        field_type=HasOne("FieldType"),
        object_type=HasOne("ObjectType"),
        sample_type=HasOne("SampleType")
    )


@add_schema
class User(ModelBase):
    """A User model"""
    fields = dict(
        groups=fields.Nested("Group", many=True, load_only=True),
        additional=("name", "id", "login"),
        ignore=("password_digest", "remember_token", "key")
    )


@add_schema
class Budget(ModelBase):
    """A Budget model"""
    fields = dict(
        user_budget_associations=HasMany("UserBudgetAssociation", "Budget")
    )


@add_schema
class Code(ModelBase):
    """A Code model"""
    fields = dict(
        user=HasOne("User")
    )

    # TODO: this is weird?
    def update(self):
        # TODO: make server side controller for code objects
        # since they may not always be tied to specific parent
        # controllers
        self.session.utils.update_code(self)


@add_schema
class Collection(ModelBase):  # pylint: disable=too-few-public-methods
    """A Collection model"""
    fields = dict(
        object_type=HasOne("ObjectType"),
        data_associations=HasManyGeneric("DataAssociation")
    )


@add_schema
class DataAssociation(ModelBase):
    """A DataAssociation model"""
    fields = dict(
        object=fields.Function(serialize=lambda x: x.object, deserialize=lambda x: json.loads(x)),
        upload=HasOne("Upload")
    )

    @property
    def value(self):
        return self.object.get(self.key, None)


@add_schema
class FieldType(ModelBase):
    """A FieldType model"""
    fields = dict(
        allowable_field_types=HasMany("AllowableFieldType", "FieldType"),
        operation_type=One("OperationType", param=lambda self: self.parent_id),
        sample_type=One("SampleType", param=lambda self: self.parent_id)
    )

    @property
    def is_parameter(self):
        return self.ftype != "sample"


@add_schema
class FieldValue(ModelBase):
    """A FieldValue model"""
    fields = dict(
        field_type=HasOne("FieldType"),
        allowable_field_type=HasOne("AllowableFieldType"),
        item=One("Item", params=lambda self: self.child_item_id),
        sample=One("Sample", params=lambda self: self.child_sample_id),
        operation=One("Operation", params=lambda self: self.parent_id),
        parent_sample=One("ParentSample", params=lambda self: self.parent_id)
    )

    def __init__(self):
        self.child_item_id = None
        self.child_sample_id = None
        self.row = None
        self.column = None
        self.role = None
        self.field_type = None
        self.allowable_field_type_id = None
        self.allowable_field_type = None
        super().__init__()


def choose_item(self):
    items = self.compatible_items()
    if items:
        self.item = items[0]
        self.child_item_id = self.item.id
        return self.item


# TODO: add compatible items
@magiclist
def compatible_items(self):
    pass


@add_schema
class Group(ModelBase):
    """A Group model"""
    pass


@add_schema
class Invoice(ModelBase):
    """A Invoice model"""
    pass


@add_schema
class Item(ModelBase):
    """A Item model"""
    fields = dict(
        sample=HasOne("Sample"),
        object_type=HasOne("ObjectType"),
        data_associations=HasManyGeneric("DataAssociation")
    )


@add_schema
class Job(ModelBase):
    """A Job model"""
    fields = dict(
        job_associations=HasMany("JobAssociation", "Job"),
        operations=HasManyThrough("Operation", "JobAssociation")
    )


@add_schema
class JobAssociation(ModelBase):
    """A JobAssociation model"""
    fields = dict(
        job=HasOne("Job"),
        operation=HasOne("Operation")
    )


@add_schema
class Sample(ModelBase):
    """A Sample model"""
    fields = dict(
        sample_type=One("SampleType", attr="sample_type_id"),
        items=Many("Item", params=lambda self: {"sample_id": self.id}),
        field_values=Many("FieldValue", params=lambda self: {
            "parent_id": self.id})
    )

    @property
    def identifier(self):
        """Return the identifier used by Aquarium in autocompletes"""
        return "{}: {}".format(self.id, self.name)

    def field_value(self, name):
        for field_value in self.field_values:
            if field_value.name == name:
                return field_value
        return None

    @property
    def field_names(self):
        return [fv.name for fv in self.field_values]


@add_schema
class SampleType(ModelBase):
    """A SampleType model"""
    fields = dict(
        samples=HasMany("Sample", "SampleType")
    )

    def create(self):
        return self.session.create.create_samples([self])


@add_schema
class Plan(ModelBase):
    """A Plan model"""
    fields = dict(
        data_associations=HasManyGeneric("DataAssociation"),
        plan_associations=HasMany("PlanAssociation", "Plan"),
        operations=Many("Operation", params=lambda self: {"id": x.operation_id for x in self.plan_associations})
    )

    def __init(self):
        self.id = None
        self.name = None
        self.status = "planning"
        self.layout = {"id": 0, "parent_id": -1, "wires": [], "name": "no_name"}
        self.operations = []
        self.source = None
        self.destination = None
        super().__init__()

    def callback(self):
        pass

    def add_operations(self, ops):
        self.operations = ops

    def wire(self, src, dest):
        self.source = src
        self.destination = dest

    def add_wires(self, pairs):
        for src, dest in pairs:
            self.wire(src, dest)

    def submit(self, user, budget):
        self.session.create.create_plan(self, user, budget)


@add_schema
class Operation(ModelBase):
    """A Operation model"""
    fields = dict(
        field_values=HasManyGeneric("FieldValue"),
        data_associations=HasManyGeneric("DataAssociation"),
        operation_type=One("OperationType"),
        job_associations=HasMany("JobAssociation", "Operation"),
        jobs=HasManyThrough("Job", "JobAssociation"),
        plan_associations=HasMany("PlanAssociation", "Operation"),
        plans=HasManyThrough("Plan", "PlanAssociation")
    )

    @property
    def plan(self):
        return self.plans[0]

    @property
    @magiclist
    def inputs(self):
        return [fv for fv in self.field_values if fv.role == 'input']

    @property
    @magiclist
    def outputs(self):
        return [fv for fv in self.field_values if fv.role == 'output']


@add_schema
class OperationType(ModelBase, HasCode):
    """A OperationType model"""
    fields = dict(
        operations=HasMany("Operation", "OperationType"),
        field_types=HasManyGeneric("Operation"),
        codes=HasManyGeneric("Code")
    )


@add_schema
class PlanAssociation(ModelBase):
    """A PlanAssociation model"""
    fields = dict(
        plan=HasOne("Plan"),
        operation=HasOne("Operation")
    )


@add_schema
class Wire(ModelBase):
    """A Wire model"""
    fields = dict(
        # load_only=False, will force dumping of FieldValues here...
        source=One("FieldValue", dump_to="from", load_only=False,
                   params=lambda self: self.from_id),
        destination=One("FieldValue", dump_to="to", load_only=False,
                        params=lambda self: self.to_id)
    )

    def show(self, pre=""):
        """Show the wire nicely"""
        print(pre + self.source.operation.operation_type.name +
              ":" + self.source.name +
              " --> " + self.destination.operation.operation_type.name +
              ":" + self.destination.name)


@add_schema
class Library(ModelBase, HasCode):
    """A Library model"""
    fields = dict(
        operations=HasMany("Operation", "Library"),
        field_types=HasManyGeneric("FieldType"),
        codes=HasManyGeneric("Code")
    )
