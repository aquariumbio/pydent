"""
Models (:mod:`pydent.models`)
=============================

.. _models:

.. currentmodule:: pydent.models

This module contains classes for various Aquarium objects.

Models are loaded and initialized from a :class:`AqSession <pydent.aqsession.AqSession>`
instance.

.. code-block:: python

    sample = session.Sample.one()
    last50 = session.Item.last(50)
    first10 = session.SampleType.first(10)
    mysamples = session.Sample.last(10, query={'user_id': 66})

.. note::
    If using an interactive developer, type `session.` and hit `[TAB]` to
    view possible models. Most models have standard method interfaces,
    such as `find`, `where`, `one`, `first`, `last`, `all`.

From a model instance, attributes can be accessed directly from the model.

.. code-block:: python

    print(sample.name)
    print(sample.id)
    # "LJk12345"
    # 3

Calling some attributes will automatically make a new *request*. For example,
calling `sample_type` from `sample` will initialize a request for information
about that sample's `sample_type`:

.. code-block:: python

    print(sample.sample_type.name)
    # "Plasmid Stock"

If we call `sample_type` again, a new request *will not be made*, rather
the model will return the previously returned data. If a new request
is desired, we can reset the field using the
:meth:`reset_field <pydent.base.ModelBase.reset_field>` method:

.. code-block:: python

    assert sample.is_deserialized('sample_type')
    sample.reset_field('sample_type')
    assert not sample.is_deserialized('sample_type')


    # now calling 'sample_type' again will initialize a new request
    # which will be cached. This can be checked using `is_deserialized`
    sample.sample_type
    assert sample.is_deserialized('sample_type')

.. versionadded:: 0.1.5a7
    :meth:`reset_field <pydent.base.ModelBase.reset_field>` method added to reset
    fields.

.. versionadded:: 0.1.5a7
    :meth:`is_deserialized <pydent.base.ModelBase.is_deserialized>` can be called
    to check if a relation has already been deserialized

Models can be dumped to their JSON data or loaded from data

.. code-block:: python

    # dump the data
    data = sample.dump()

    # load from the data
    sample2 = session.Sample.load(data)

.. warning::
    Most model methods require an attached :class:`Session <pydent.aqsession.AqSession>`
    instance. Importing models from *pydent.models* will result in orphaned models.
    Preferrably, if you need to initialize or load new models, use
    `session.<ModelName>(*args, **kwargs)`, replacing <ModelName> with the name
    of the model class. Alternatively, you can attach a Session instance using
    :meth:`model.connect_to_session(session) <pydent.base.ModelBase.connect_to_session>`

Model Classes
-------------

Operations
^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    Operation
    OperationType
    Code
    Library
    Job
    JobAssociation

Plans
^^^^^

.. autosummary::
    :toctree: generated/

    Plan
    PlanAssociation
    Wire

Inventory
^^^^^^^^^

.. autosummary::
    :toctree: generated/

    Item
    Collection
    ObjectType
    Sample
    SampleType
    PartAssociation

Data and IO
^^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    DataAssociation
    FieldValue
    FieldType
    AllowableFieldType

User
^^^^

.. autosummary::
    :toctree: generated/

    Account
    Budget
    Group
    Invoice
    Membership
    User
    UserBudgetAssociation

Model Mixins
------------

.. currentmodule:: pydent.models

These classes provide some models with common methods such as saving or deleting
models from the server or associating data.

.. autosummary::
    :toctree: generated/

    crud_mixin.CreateMixin
    crud_mixin.DeleteMixin
    crud_mixin.JSONDeleteMixin
    crud_mixin.JSONSaveMixin
    crud_mixin.SaveMixin
    crud_mixin.UpdateMixin
    data_associations.DataAssociatorMixin
    field_value_mixins.FieldMixin
    field_value_mixins.FieldTypeInterface
    field_value_mixins.FieldValueInterface


Field Relationships
-------------------

.. currentmodule:: pydent.relationships

Field relationships are attribute descriptors that may call
information from the Aquarium server if necesssary.

.. autosummary::
    :toctree: generated/

    BaseRelationship
    BaseRelationshipAccessor
    Function
    HasMany
    HasManyGeneric
    HasManyThrough
    HasOne
    HasOneFromMany
    JSON
    Many
    One
    Raw

Exceptions
^^^^^^^^^^

.. autosummary::
    :toctree: generated/

    FieldValidationError

Utilities
---------

.. currentmodule:: pydent.marshaller

.. autosummary::
    :toctree: generated/

    add_schema
"""
from pydent.models.code import Code
from pydent.models.code import Library
from pydent.models.data_associations import DataAssociation
from pydent.models.data_associations import Upload
from pydent.models.field_value import AllowableFieldType
from pydent.models.field_value import FieldType
from pydent.models.field_value import FieldValue
from pydent.models.inventory import Collection
from pydent.models.inventory import Item
from pydent.models.inventory import ObjectType
from pydent.models.inventory import PartAssociation
from pydent.models.job import Job
from pydent.models.job import JobAssociation
from pydent.models.operation import Operation
from pydent.models.operation import OperationType
from pydent.models.plan import Plan
from pydent.models.plan import PlanAssociation
from pydent.models.plan import Wire
from pydent.models.sample import Sample
from pydent.models.sample import SampleType
from pydent.models.user import Account
from pydent.models.user import Budget
from pydent.models.user import Group
from pydent.models.user import Invoice
from pydent.models.user import Membership
from pydent.models.user import User
from pydent.models.user import UserBudgetAssociation

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
    "Wire",
]
