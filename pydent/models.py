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

from pydent.modelbase import ModelBase
from pydent.relationships import One, Many, HasOne, HasMany
from pydent.marshaller import add_schema


@add_schema
class Account(ModelBase):
    pass


@add_schema
class AllowableFieldType(ModelBase):
    class Fields:
        field_type = HasOne("FieldType")
        object_type = HasOne("ObjectType")
        sample_type = HasOne("SampleType")


@add_schema
class User(ModelBase):
    class Fields:
        groups = fields.Nested("Group", many=True, load_only=True)
        additional = ("name", "id", "login")
        ignore = ("password_digest", "remember_token", "key")


@add_schema
class Budget(ModelBase):
    class Fields:
        user_budget_associations = HasMany("UserBudgetAssociation", "Budget")


@add_schema
class Code(ModelBase):
    class Fields:
        user = HasOne("User")

    def update(self):
        self.session.update.code(self)


@add_schema
class Collection(ModelBase):
    class Fields:
        object_type = HasOne("ObjectType")
        data_associations = Many("DataAssociation", params={
            "parent_id": lambda self: self.id})


@add_schema
class DataAssociation(ModelBase):
    class Fields:
        upload = HasOne("Upload")

    @property
    def value(self):
        obj = json.loads(self.object)
        return obj.get(self.key, None)


@add_schema
class FieldType(ModelBase):
    class Fields:
        allowable_field_types = HasMany("AllowableFieldType", "FieldType")
        operation_type = One("OperationType", param=lambda self: self.parent_id)
        sample_type = One("SampleType", param=lambda self: self.parent_id)

    @property
    def is_parameter(self):
        return self.ftype != "sample"


@add_schema
class FieldValue(ModelBase):
    class Fields:
        field_type = HasOne("FieldType")
        allowable_field_type = HasOne("AllowableFieldType")
        item = One("Item", attr=lambda self: self.child_item_id)
        sample = One("Sample", attr=lambda self: self.child_sample_id)
        operation = One("Operation", attr=lambda self: self.parent_id)
        parent_sample = One("ParentSample", attr=lambda self: self.parent_id)

    def __init__(self, data=None):
        super().__init__(data=data)
        self.value = None
        self.child_item_id = None
        self.child_sample_id = None
        self.row = None
        self.column = None
        self.role = None
        self.field_type = None
        self.allowable_field_type_id = None
        self.allowable_field_type = None

    def choose_item(self):
        items = self.compatible_items()
        if items:
            self.item = items[0]
            self.child_item_id = self.item.id
            return self.item

    # TODO: add compatible items
    def compatible_items(self):
        pass


@add_schema
class Group(ModelBase):
    pass


@add_schema
class Invoice(ModelBase):
    pass


@add_schema
class Item(ModelBase):
    class Fields:
        sample = HasOne("Sample")
        object_type = HasOne("ObjectType")
        data_associations = HasMany("DataAssociation", "Item")


@add_schema
class Job(ModelBase):
    class Fields:
        job_associations = HasMany("JobAssociation", "Job")
        # operations = Many("Operation",
        #                   params=lambda self: [ja.job_id for ja in self.job_associations])


@add_schema
class JobAssociation(ModelBase):
    class Fields:
        job = HasOne("Job")
        operation = HasOne("Operation")


@add_schema
class Sample(ModelBase):
    class Fields:
        sample_type = One("SampleType", attr="sample_type_id")
        items = Many("Item", params=lambda self: {"sample_id": self.id})
        field_values = Many("FieldValue", params=lambda self: {
            "parent_id": self.id})

    @property
    def identifier(self):
        """Return the identifier used by Aquarium in autocompletes"""
        return "{}: {}".format(self.id, self.name)


@add_schema
class SampleType(ModelBase):
    class Fields:
        samples = HasMany("Sample", "SampleType")
        # samples = Many("Sample", params=lambda self: {"sample_type_id": self.id})

    def create(self):
        return self.session.create.samples([self])


@add_schema
class Plan(ModelBase):
    class Fields:
        data_associations = Many("DataAssociation", params={
            "parent_id": lambda self: self.id})

    def __init__(self, data=None):
        super().__init__(data=data)
        self.id = None
        self.name = None
        self.status = "planning"
        self.layout = {"id": 0, "parent_id": -1, "wires": [], "name": "no_name"}
        self.operations = []
        self.source = None
        self.destination = None

    def add_operations(self, ops):
        self.operations = ops

    def wire(self, src, dest):
        self.source = src
        self.destination = dest

    def add_wires(self, pairs):
        for src, dest in pairs:
            self.wire(src, dest)

    def submit(self, user, budget):
        self.session.create.plan(self, user, budget)
