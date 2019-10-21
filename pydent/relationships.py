"""
Relationships (:mod:`pydent.relationships`)
===========================================

.. currentmodule:: pydent.relationships

.. autosummary::
    :toctree: generated/

    BaseRelationship
    BaseRelationshipAccessor
    Function
"""
import json

import inflection

from pydent.base import ModelBase
from pydent.marshaller import fields
from pydent.marshaller.exceptions import ModelValidationError


class FieldValidationError(ModelValidationError):
    pass


class Raw(fields.Field):
    """Field that performs no serialization/deserialization."""

    def __init__(self, many=False, data_key=None, allow_none=True, default=None):
        super().__init__(
            many=many, data_key=data_key, allow_none=allow_none, default=default
        )


class JSON(Raw):
    """Automatically serializes/deserializes JSON objects."""

    def _deserialize(self, owner, data):
        if isinstance(data, dict):
            return data
        return json.loads(data)

    def _serialize(self, owner, data):
        return json.dumps(data)


class Function(fields.Callback):
    """Calls a specified function upon attribute access.

    Similar to the @property decorator in python, but will search and
    find an instance method using the method name.
    """

    def __init__(
        self,
        callback,
        callback_args=None,
        callback_kwargs=None,
        cache=False,
        data_key=None,
        many=None,
        allow_none=True,
        always_dump=True,
    ):
        super().__init__(
            callback,
            callback_args,
            callback_kwargs,
            cache,
            data_key,
            many,
            allow_none,
            always_dump,
        )


class BaseRelationshipAccessor(fields.RelationshipAccessor):
    """Python descriptor that is returned by a field during attribute
    access."""

    HOLDER = None


class BaseRelationship(fields.Relationship):
    """Base class for relationships.

    By default, if the value is None, attempt a callback. If that fails,
    fallback to None. If successful, deserialize data to the nested
    model.
    """

    QUERY_TYPE = None
    ACCESSOR = BaseRelationshipAccessor

    def __init__(
        self,
        nested,
        callback,
        ref,
        attr,
        callback_args=None,
        callback_kwargs=None,
        many=None,
        allow_none=True,
    ):
        if (ref is None and attr is not None) or (attr is None and ref is not None):
            raise ModelValidationError(
                "ref={} is None while attr={}."
                "Either both must be provided or both absent".format(ref, attr)
            )
        elif attr is None and ref is None:
            ref, att = self._get_ref_attr(nested=nested, ref=ref, attr=attr)
        self.attr = attr
        self.ref = ref
        super().__init__(
            nested,
            callback,
            callback_args,
            callback_kwargs,
            cache=True,
            data_key=None,
            many=many,
            allow_none=allow_none,
        )

    def _get_ref_attr(self, nested=None, ref=None, attr=None):
        """Sets the 'ref' and 'attr' attributes. These attributes are used to
        defined parameters for.

        :class:`pydent.marshaller.Relation` classes.

        For example:

        .. code-block:: python

            relation # HasOne, HasMany, or HasManyGeneric, etc.
            relation.set_ref(ref="parent_id")
            relation.ref    # "parent_id"
            relation.attr   # "id"

            relation.set_ref(model="SampleType")
            relation.ref   # "sample_type_id"
            relation.attr  # "id"

            relation.set_ref(attr="name", model="OperationType")
            relation.ref   # "operation_type_name
            relation.attr  # "name"
        """

        if not attr:
            attr = "id"
        if ref:
            ref = ref
        else:
            if not attr:
                raise FieldValidationError(
                    "'attr' is None. Relationship '{}' needs an 'attr' and 'model' "
                    "parameters".format(self.__class__)
                )
            if not nested:
                raise FieldValidationError(
                    "'model' is None. Relationship '{}' needs an 'attr' and 'model' "
                    "parameters".format(self.__class__)
                )
            ref = "{}_{}".format(inflection.underscore(nested), attr)
        return ref, attr

    def fullfill(self, owner, cache=None, extra_args=None, extra_kwargs=None):
        try:
            return super().fullfill(
                owner, cache, extra_args=extra_args, extra_kwargs=extra_kwargs
            )
        except fields.RunTimeCallbackAttributeError:
            return BaseRelationshipAccessor.HOLDER

    def build_query(self, models):
        """Bundles all of the callback args for the models into a single
        query."""
        args = {}
        for s in models:
            callback_args = self.get_callback_args(s)[1:]
            if self.QUERY_TYPE == "by_id":
                args.setdefault(self.attr, [])
                for x in callback_args:
                    if x is not None and x not in args[self.attr]:
                        args[self.attr].append(x)
            else:
                for cba in callback_args:
                    for k in cba:
                        args.setdefault(k, [])
                        arg_arr = args[k]
                        val = cba[k]
                        if val is not None:
                            if isinstance(val, list):
                                for v in val:
                                    if v not in arg_arr:
                                        arg_arr.append(v)
                            elif val not in arg_arr:
                                arg_arr.append(val)
        return args


class One(BaseRelationship):
    """Defines a single relationship with another model.

    Subclass of :class:`pydent.marshaller.Relation`.
    """

    QUERY_TYPE = "by_id"

    def __init__(
        self,
        nested,
        ref=None,
        attr=None,
        callback=None,
        callback_args=None,
        callback_kwargs=None,
        **kwargs,
    ):
        """One initializer. Uses "find" callback by default.

        :param nested: target model
        :type nested: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        if callback is None:
            callback = ModelBase.find_callback.__name__
        super().__init__(
            nested,
            callback,
            ref=ref,
            attr=attr,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            many=False,
        )


class Many(BaseRelationship):
    """Defines a many relationship with another model.

    Subclass of :class:`pydent.marshaller.Relation`.
    """

    QUERY_TYPE = "query"

    def __init__(
        self,
        nested,
        ref=None,
        attr=None,
        callback=None,
        callback_args=None,
        callback_kwargs=None,
        **kwargs,
    ):
        """Many initializer. Uses "where" callback by default.

        :param nested: target model
        :type nested: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        if callback is None:
            callback = ModelBase.where_callback.__name__
        super().__init__(
            nested,
            ref=ref,
            attr=attr,
            many=True,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            **kwargs,
        )


class HasOne(One):
    def __init__(
        self, nested, attr=None, ref=None, callback=None, callback_kwargs=None, **kwargs
    ):
        """HasOne initializer. Uses the "get_one_generic" callback and
        automatically assigns attribute as in the following:

        .. code-block:: python

            # equiv. to 'lambda self: self.sample_type_id.'
            model="SampleType", attr="id"

        :param nested: model name of the target model
        :type nested: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """
        ref, attr = self._get_ref_attr(nested=nested, attr=attr, ref=ref)
        self.ref = ref
        self.attr = attr

        super().__init__(
            nested,
            self.ref,
            self.attr,
            many=False,
            callback=callback,
            callback_args=(self.get_ref,),
            callback_kwargs=callback_kwargs,
            **kwargs,
        )

    def get_ref(self, instance):
        return getattr(instance, self.ref)

    def __repr__(self):
        return "<HasOne (model={}, callback_args=lambda self: self.{})>".format(
            self.nested, self.ref
        )

    def deserialize(self, owner, val):
        val = super().deserialize(owner, val)
        if val:
            setattr(owner, self.ref, getattr(val, self.attr))
        return val


class HasMany(Many):
    """A relationship that establishes a One-to-Many relationship with another
    model."""

    def __init__(
        self,
        nested,
        ref_model=None,
        attr=None,
        ref=None,
        additional_args=None,
        callback=None,
        callback_kwargs=None,
        **kwargs,
    ):
        """HasMany relationship initializer.

        :param nested: Model class name for this relationship
        :type nested: str
        :param ref_model: Reference model name of the model owning this relationships.

        .. code-block:: python

            @add_schema
            class Author(ModelBase):
                fields=dict(books=HasMany("Book", "Author"))  # search for books using 'author_id'

        :type ref_model: str
        :param attr: Attribute name to use with reference model (default='id').
                     For example "Author" => 'author_id'
        :type attr: str
        :param ref: The reference to use to find models. If none, a reference is
                    built from the 'ref_model' and 'attr' parameters
        :type ref: str
        """
        if ref_model is None and ref is None:
            msg = "'{}' needs a 'ref_model' or 'ref' parameters to initialize"
            raise FieldValidationError(msg.format(self.__class__.__name__))
        ref, attr = self._get_ref_attr(nested=ref_model, attr=attr, ref=ref)
        self.ref = ref
        self.attr = attr

        if additional_args is None:
            additional_args = {}

        def callback_args(slf):
            query = {self.ref: getattr(slf, self.attr)}
            query.update(additional_args)
            return query

        super().__init__(
            nested,
            ref=self.ref,
            attr=self.attr,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            **kwargs,
        )


class HasManyThrough(Many):
    """A relationship using an intermediate association model.

    Establishes a Many-to-Many relationship with another model
    """

    def __init__(
        self,
        nested,
        through,
        attr="id",
        ref=None,
        additional_args=None,
        callback=None,
        callback_kwargs=None,
        **kwargs,
    ):
        ref, attr = self._get_ref_attr(nested=nested, attr=attr, ref=ref)
        self.ref = ref
        self.attr = attr

        # e.g. PlanAssociation >> plan_associations
        through_model_attr = inflection.pluralize(inflection.underscore(through))
        self.through_model_attr = through_model_attr

        if additional_args is None:
            additional_args = {}

        def callback_args(slf):
            through_model = getattr(slf, through_model_attr)
            if through_model is None:
                return None
            query = {
                attr: [getattr(x, self.ref) for x in getattr(slf, through_model_attr)]
            }
            query.update(additional_args)
            return {
                attr: [getattr(x, self.ref) for x in getattr(slf, through_model_attr)]
            }

        super().__init__(
            nested,
            ref=self.ref,
            attr=self.attr,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            **kwargs,
        )


class HasOneFromMany(One):
    """Returns a single model from a Many relationship."""

    QUERY_TYPE = "query"

    def __init__(
        self,
        nested,
        ref_model=None,
        attr=None,
        ref=None,
        additional_args=None,
        callback=None,
        callback_kwargs=None,
        **kwargs,
    ):
        """HasOneFromMany relationship initializer, which is intended to return
        a single model from a Many query.

        :param nested: Model class name for this relationship
        :type nested: str
        :param ref_model: Reference model name of the model owning this relationships.

        .. code-block:: python

            @add_schema
            class Author(ModelBase):
                # search for books using 'author_id'
                fields=dict(books=HasMany("Book", "Author"))

        :type ref_model: str
        :param attr: Attribute name to use with reference model (default='id').
                     For example "Author" => 'author_id'
        :type attr: str
        :param ref: The reference to use to find models. If none, a reference is
                    built from the 'ref_model' and 'attr' parameters
        :type ref: str
        """
        if ref_model is None and ref is None:
            msg = "'{}' needs a 'ref_model' or 'ref' parameters to initialize"
            raise FieldValidationError(msg.format(self.__class__.__name__))
        ref, attr = self._get_ref_attr(nested=ref_model, attr=attr, ref=ref)
        self.ref = ref
        self.attr = attr

        if additional_args is None:
            additional_args = {}

        def callback_args(slf):
            query = {self.ref: getattr(slf, self.attr)}
            query.update(additional_args)
            return query

        if callback is None:
            callback = ModelBase.one_callback.__name__

        super().__init__(
            nested,
            ref=self.ref,
            attr=self.attr,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            **kwargs,
        )


class HasManyGeneric(HasMany):
    """Establishes a One-to-Many relationship using 'parent_id' as the
    attribute to find other models."""

    def __init__(
        self,
        nested,
        additional_args=None,
        callback=None,
        callback_kwargs=None,
        **kwargs,
    ):
        super().__init__(
            nested,
            ref="parent_id",
            attr="id",
            callback=callback,
            additional_args=additional_args,
            callback_kwargs=callback_kwargs,
            **kwargs,
        )
