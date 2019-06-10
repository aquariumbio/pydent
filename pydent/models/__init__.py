"""Aquarium models

This module contains a set of classes for various various Aquarium objects.
Trident models inherit the ModelBase class and have a model schema
(generated by ``@add_schema``) that handles the JSON loading and dumping.

By default, Trident models capture ALL JSON attribute/values and sets
the attributes of the resultant object.

. code-block:: python

    u = User.load({"id": 1, "login": "John"})
    u.login    # => "John"
    u.id       # => 1

Fields and field options are added as class variables in the model class
definition.
The various field options and their default values are listed below.

. code-block:: python

        load_all = True     # load all data attributes defined for a model
        strict = True       # throw error during marshalling
        include = {}        # fields to include for serialization
        additional = ()     # explicit fields for serialization
        ignore = ()         # fields to filter during deserialization.
        load_only = ()      # fields to include during serialization
        dump_only = ()      # fields to include during deserialization

Trident models can also have nested relationships (for example, a Sample may
possess a single SampleType while a SampleType may possess several Samples).
These relationships can be specified in the class definition along with the
field options above, as in:

. code-block:: python

    @add_schema
    class SampleType(Base):
        samples = fields.Nested("Sample", many=True)

In many cases, the model contains only a reference to the nested relationship,
in this case, special fields One and Many may be used to define this
relationship.
When called as an attribute, Trident will automatically use the session
connection with Aquarium to retrieve the given model.

For example, the following will define that SampleType has many Samples.
When .samples is called on a SampleType instance, Trident will use the database
to retrieve all samples that have a sample_type_id equal to the id of the
SampleType:

. code-block:: python

    @add_schema
    class SampleType(Base):
        samples = Many("Sample",
            callback_args={"sample_type_id": lambda self: self.id})
"""

from pydent.models.code import Code, Library
from pydent.models.data_associations import DataAssociation, Upload
from pydent.models.field_value import FieldValue, FieldType, AllowableFieldType
from pydent.models.inventory import Item, Collection, ObjectType, PartAssociation
from pydent.models.job import Job, JobAssociation
from pydent.models.operation import Operation, OperationType
from pydent.models.plan import Plan, PlanAssociation, Wire
from pydent.models.sample import Sample, SampleType
from pydent.models.user import Account, Budget, Group, Invoice, Membership, User, UserBudgetAssociation

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
    "PartAssociation",
    "Plan",
    "PlanAssociation",
    "Sample",
    "SampleType",
    "Upload",
    "User",
    "UserBudgetAssociation",
    "Wire"
]
