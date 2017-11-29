"""Aquarium models

This module contains a set of classes for various various Aquarium objects. Trident models
inherit the Base class and have a model schema (handled by '@add_schema`) that handles
the JSON loading and dumping.

By default, Trident models capture ALL JSON attribute/values and sets the attributes to the
resultant object.

.. code-block:: python

    u = User.load({"id": 1, "login": "John"})
    u.login    # => "John"
    u.id       # => 1

Fields and field options are added as class variables in the model class definition.
Below lists various field options and their default values.

.. code-block:: python

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

.. code-block:: python

    @add_schema
    class SampleType(Base):
        samples = fields.Nested("Sample", many=True)

In many cases, the model contains only a reference to the nested relationship, in this case, special fields
One and Many may be used to define this relationship. When called as an attribute, Trident will automatically
use the session connection with Aquarium to retrieve the given model.

For example, the following will define that SampleType has many Samples. When .samples is called on a
SampleType instance, Trident will use the database to retrieve all samples that have a sample_type_id
equal to the id of the SampleType:

.. code-block:: python

    @add_schema
    class SampleType(Base):
        samples = Many("Sample", params={"sample_type_id": lambda self: self.id})
"""

import json

import requests
from marshmallow import fields

from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import One, Many, HasOne, HasMany, HasManyThrough, HasManyGeneric
from pydent.utils import magiclist

__all__ = [
    "Account",
    "AllowableFieldType",
    "Budget",
    "Code",
    "Collection",
    "DataAssociation",
    "FieldType",
    "FieldValue",
    "Group",
    "Invoice",
    "Item",
    "Job",
    "JobAssociation",
    "Library",
    "Membership",
    "ObjectType",
    "Operation",
    "OperationType",
    "Plan",
    "PlanAssociation",
    "Sample",
    "SampleType",
    "Upload",
    "User",
    "UserBudgetAssociation",
    "Wire"
]


##### Mixins #####

class HasCode(object):
    """Access to latest code for OperationType, Library, etc."""

    def code(self, name):
        codes = [c for c in self.codes if c.name == name]
        codes = [c for c in codes if not hasattr(c, "child_id") or c.child_id is None]
        return codes[-1]


class FieldMixin(object):
    """Mixin for finding FieldType and FieldValue relationships"""

    def find_field_parent(self, model_name, id):
        """Callback for finding operation_type or sample_type. If parent_class does not match
        the expected nested model name (OperationType or SampleType), callback will return
        None"""
        if model_name == self.parent_class:
            # weird, but helps with refactoring this mixin
            fxn_name = ModelBase.find_using_session.__name__
            fxn = getattr(self, fxn_name)
            return fxn(model_name, id)

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
class FieldType(ModelBase, FieldMixin):
    """A FieldType model"""
    fields = dict(
        allowable_field_types=HasMany("AllowableFieldType", "FieldType"),
        operation_type=One("OperationType", callback="find_field_parent", params=lambda self: self.parent_id),
        sample_type=One("SampleType", callback="find_field_parent", params=lambda self: self.parent_id)
    )

    @property
    def is_parameter(self):
        return self.ftype != "sample"


@add_schema
class FieldValue(ModelBase, FieldMixin):
    """A FieldValue model"""
    fields = dict(
        # FieldValue relationships
        field_type=HasOne("FieldType"),
        allowable_field_type=HasOne("AllowableFieldType"),
        item=One("Item", params=lambda self: self.child_item_id),
        sample=One("Sample", params=lambda self: self.child_sample_id),
        operation=One("Operation", callback="find_field_parent", params=lambda self: self.parent_id),
        parent_sample=One("Sample", callback="find_field_parent", params=lambda self: self.parent_id),

        # ignore object_type
        ignore=("object_type",)


    )

    def __init__(self, parent_class=None, value=None, sample=None, container=None, item=None):
        """

        :param value:
        :type value:
        :param sample:
        :type sample:
        :param container:
        :type container:
        :param item:
        :type item:
        """
        # self.parent_class = parent_class
        # self.child_item_id = None
        # self.child_sample_id = None
        # self.item = None
        # self.sample = None
        # self.value = None
        # self.row = None
        # self.column = None
        # self.role = None
        # self.field_type = None
        # self.allowable_field_type_id = None
        # self.allowable_field_type = None
        # self.set_value(value, sample, container, item)
        super().__init__()

    def show(self, pre=""):
        if self.sample:
            if self.child_item_id:
                item = " item: {}".format(self.child_item_id) + \
                       " in {}".format(self.item.object_type.name)
            else:
                item = ""
            print('{}{}.{}:{}{}'.format(pre, self.role, self.name, self.sample.name, item))
        elif self.value:
            print('{}{}.{}:{}'.format(pre, self.role, self.name, self.value))

    def _set_sample(self, sample):
        self.sample = sample
        self.child_sample_id = sample.identifier

        for aft in self.field_type.allowable_field_types:
            if sample.sample_type_id == aft.sample_type_id:
                aft.sample_type = sample.sample_type
                self.allowable_field_type_id = aft.id
                self.allowable_field_type = aft

    def _set_value(self, value):
        self.value = value

    def _set_item(self, item):
        self.item = item
        self.child_item_id = item.id
        self.object_type = item.object_type
        for aft in self.field_type.allowable_field_types:
            if item.object_type.id == aft.object_type_id:
                aft.object_type = item.object_type
                self.allowable_field_type_id = aft.id
                self.allowable_field_type = aft

    def _set_container(self, container):
        self.object_type = container
        for aft in self.field_type.allowable_field_types:
            if container.id == aft.object_type_id:
                aft.object_type = container
                self.allowable_field_type_id = aft.id
                self.allowable_field_type = aft

    def _set_afts(self):
        for aft in self.field_type.allowable_field_types:
            if self.sample:
                if self.sample.sample_type_id == aft.sample_type_id:
                    self.allowable_field_type_id = aft.id
                    self.allowable_field_type = aft
            elif self.object_type:
                if self.object_type.id == aft.object_type_id:
                    self.allowable_field_type_id = aft.id
                    self.allowable_field_type = aft

    def set_value(self, value=None, sample=None, container=None, item=None):
        if item and container and item.object_type_id != container.id:
            raise Exception("Item {} is not in container {}".format(item.id, container.name))

        if container:
            self._set_container(container)

        if item:
            self._set_item(item)

        if sample:
            self._set_sample(sample)

        if value:
            self._set_value(value)

        if not self.allowable_field_type:
            if sample or item or container:
                raise Exception("No allowable field type found for {} {}".format(self.role, self.name))

        return self


    def choose_item(self):
        """Set the item associated with the field value"""
        items = self.compatible_items()
        if len(items) > 0:
            self.child_item_id = items[0].id
            self.item = items[0]
            return items[0]
        return None


    def compatible_items(self):
        """Find items compatible with the field value"""
        result = self.session.aqhttp.post("/json/items", {
            "sid": self.sample.id,
            "oid": self.allowable_field_type.object_type_id})
        items = []
        for element in result:
            if "collection" in element:
                items.append(aq.Collection.record(element["collection"]))
            else:
                items.append(aq.Item.record(element))
        return items


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
class Library(ModelBase, HasCode):
    """A Library model"""
    fields = dict(
        codes=HasManyGeneric("Code")
    )


@add_schema
class Membership(ModelBase):
    fields = dict(
        user=HasOne("User"),
        group=HasOne("Group")
    )


@add_schema
class ObjectType(ModelBase):
    """A ObjectType model"""


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
        field_types=HasManyGeneric("FieldType"),
        codes=HasManyGeneric("Code")
    )


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
class PlanAssociation(ModelBase):
    """A PlanAssociation model"""
    fields = dict(
        plan=HasOne("Plan"),
        operation=HasOne("Operation")
    )


@add_schema
class Sample(ModelBase):
    """A Sample model"""
    fields = dict(
        # sample relationships
        sample_type=HasOne("SampleType"),
        items=Many("Item", params=lambda self: {"sample_id": self.id}),
        field_values=Many("FieldValue", params=lambda self: {
            "parent_id": self.id}),

        # explicitly defined fields for initializing samples
        name=fields.String(),
        sample_type_id=fields.Int(),
        project=fields.String()
    )

    def __init__(self, name=None, project=None, sample_type_id=None):
        vars(self).update(locals())
        super().__init__()

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
        samples=HasMany("Sample", "SampleType"),
        field_types=Many("FieldType",
                         params=lambda self: {"parent_id": self.id, "parent_class": self.__class__.__name__})
    )

    def create(self):
        return self.session.create.create_samples([self])


@add_schema
class Upload(ModelBase):
    """An Upload model"""

    @property
    def temp_url(self):
        return self.session.Upload.where_using_session({"id", self.id}, {"methods": ["url"]})[0].url

    @property
    def data(self):
        result = requests.get(self.temp_url)
        return result.content


@add_schema
class User(ModelBase):
    """A User model"""
    fields = dict(
        groups=HasMany("Group", "User"),
        additional=("name", "id", "login"),
        ignore=("password_digest", "remember_token", "key")
    )


@add_schema
class UserBudgetAssociation(ModelBase):
    """An association model between a User and a Budget"""
    fields = dict(
        budget=HasOne("Budget"),
        user=HasOne("User")
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
