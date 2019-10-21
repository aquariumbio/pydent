"""
Serialization (:mod:`pydent.marshaller`)
========================================================

.. versionadded 0.1
    This module replaces the much slower Marshmallow library. Speed improvements >10X.

.. currentmodule:: pydent.marshaller

This module provides speedy serialization and deserialization
functionality for Trident models. Models that inherit the
:class:`SchemaModel <pydent.marshaller.base.SchemaModel>` will
become registered with their own serialization/deserialization
schema. To register the schema,
use the :meth:`add_schema <pydent.marshaller.base.add_schema>`
decorator on the class. The
:meth:`dump <pydent.marshaller.base.SchemaModel.dump>` method will serialize
and object while the :meth:`dump <pydent.marshaller.base.SchemaModel.load>` method
will deserialize JSON data to an object.

.. note::
    This is only relevant to Trident **developers**, rather than regular users.

.. autosummary::
    :toctree: generated/

    SchemaModel
    ModelRegistry
    SchemaRegistry
    descriptors
    exceptions
    utils

Fields
------

.. currentmodule:: pydent.marshaller.fields

Fields are descriptors that control how attributes and data is serialized/deserialized.

.. autosummary::
    :toctree: generated/

    Alias
    Callback
    Field
    FieldABC
    Nested
    Relationship
"""
from pydent.marshaller import descriptors
from pydent.marshaller import exceptions
from pydent.marshaller import fields
from pydent.marshaller.base import add_schema
from pydent.marshaller.base import SchemaModel
from pydent.marshaller.registry import ModelRegistry
from pydent.marshaller.registry import SchemaRegistry
