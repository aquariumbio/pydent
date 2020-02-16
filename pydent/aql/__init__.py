"""aql.py.

Aquarium Query Language

Aquarium Query Language (:mod:`pdyent.aql`)
=============================

Validated JSON Schemas (https://json-schema.org/)

Check out the :ref:`JSON Schema page <json_schema>` for more information.
"""
import json
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from os.path import abspath
from os.path import dirname
from os.path import join
from typing import Dict
from typing import List
from typing import Union

import jsonschema

from pydent.base import ModelBase
from pydent.exceptions import AquariumQueryLanguageValidationError
from pydent.relationships import HasMany
from pydent.relationships import HasOne
from pydent.sessionabc import SessionABC

aql_schema_filepath = join(abspath(dirname(__file__)), "aql.schema.json")
with open(aql_schema_filepath, "r") as f:
    aql_schema = json.load(f)


class QueryBuilder:
    AND = " AND "
    OR = " OR "

    class Op:
        op = "="

        def __init__(self, v):
            self.v = v

    class Eq(Op):
        op = "="

    class Not(Op):
        op = "!="

    class Lt(Op):
        op = "<"

    class Gt(Op):
        op = ">"

    class Gte(Op):
        op = ">="

    class Lte(Op):
        op = "<="

    @classmethod
    def _parse_key_val(cls, k, v):
        if issubclass(v.__class__, cls.Op):
            return '{} {} "{}"'.format(k, v.op, v.v)
        else:
            return '{} {} "{}"'.format(k, cls.Eq.op, v)

    @classmethod
    def sql(cls, data):
        rows = []
        for k, v in data.items():
            if isinstance(v, list) or isinstance(v, tuple) or isinstance(v, set):
                parts = [cls._parse_key_val(k, _v) for _v in v]
                rows.append("( {} )".format(cls.OR.join(parts)))
            else:
                rows.append(cls._parse_key_val(k, v))
        return cls.AND.join(rows)


def validate_with_schema(
    data: Dict, schema: Dict, do_raise: bool = True, reraise_as: Exception = None
):
    """Validate JSON data using a JSON Schema."""
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        if do_raise:
            if reraise_as:
                raise reraise_as(str(e)) from e
            else:
                raise e
        else:
            return False
    return True


operators = {
    "__not__": QueryBuilder.Not,
    "__lt__": QueryBuilder.Lt,
    "__gt__": QueryBuilder.Gt,
    "__le__": QueryBuilder.Lte,
    "__ge__": QueryBuilder.Gte,
}


def _parse_time(v):
    timedelta_kwargs = {}

    for k in ["days", "seconds", "minutes", "hours", "weeks"]:
        key = "__{}__".format(k)
        if key in v:
            timedelta_kwargs[k] = v[key]

    return str(datetime.now() + timedelta(**timedelta_kwargs))


def parse_value(v):
    if isinstance(v, dict):
        if "__time__" in v:
            return _parse_time(v)
        else:
            for op in operators:
                if op in v:
                    return operators[op](parse_value(v[op]))
    else:
        return deepcopy(v)


def _aql(session, data, model=None):
    # parse query
    model_name = data.get("__model__", model)
    interface = getattr(session, model_name)
    new_query = {}
    for k in data["query"]:
        if k.startswith("__") and k.endswith("__"):
            continue
        if k in interface.model.fields:
            field = interface.model.fields[k]
            models = _aql(session, data["query"][k], model=field.nested)
            if issubclass(field.__class__, HasMany):
                new_query[field.attr] = [getattr(m, field.ref) for m in models]
            elif issubclass(field.__class__, HasOne):
                new_query[field.ref] = [getattr(m, field.attr) for m in models]
            else:
                raise ValueError("Field '{}' not supported".format(field.__class__))
        else:
            new_query[k] = parse_value(data["query"][k])

    # make options
    opts = {"reverse": True}
    if "__options__" in data["query"]:
        opts.update(deepcopy(data["query"]["__options__"]))

    # do query
    for k, v in new_query.items():
        if issubclass(type(v), QueryBuilder.Op):
            new_query = QueryBuilder.sql(new_query)
            break

    returned_models = interface.where(new_query, opts=opts)

    # return models
    if "__return__" in data["query"]:
        session.browser.get(returned_models, data["query"]["__return__"])
    if data.get("__as__", None) == "json":
        return [m._get_data() for m in returned_models]
    else:
        return returned_models


def validate_aql(data):
    validate_with_schema(
        data, aql_schema, reraise_as=AquariumQueryLanguageValidationError
    )


def aql(
    session: SessionABC, data: Dict, use_cache: bool = False
) -> Union[List[ModelBase], Dict]:
    """Perform a complex query a complex JSON query object.

    Check out the :ref:`JSON Schema page <json_schema>` for more information.

    :param session: Aquarium session instance
    :param data: data query
    :param use_cache: whether to inherit the cache from the provided session (default: False)
    :return:
    """
    validate_aql(data)
    with session.with_cache(using_models=use_cache) as sess:
        return _aql(sess, data)
