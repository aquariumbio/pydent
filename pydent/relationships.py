"""
Model relationships
"""

import inflection
from pydent.marshaller import fields
from pydent.base import ModelBase
from pydent.marshaller.exceptions import MarshallerRelationshipError
from pydent.utils import MagicList

class One(fields.Relation):
    """Defines a single relationship with another model. Subclass of :class:`pydent.marshaller.Relation`."""

    def __init__(self, model, *args, callback=None, params=None, **kwargs):
        """
        One initializer. Uses "find" callback by default.

        :param model: target model
        :type model: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        if callback is None:
            callback = ModelBase.find_callback.__name__
        super().__init__(model, *args, callback=callback, params=params, **kwargs)


class Many(fields.Relation):
    """Defines a many relationship with another model. Subclass of :class:`pydent.marshaller.Relation`."""

    def __init__(self, model, *args, callback=None, params=None, **kwargs):
        """
        Many initializer. Uses "where" callback by default.

        :param model: target model
        :type model: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        if callback is None:
            callback = ModelBase.where_callback.__name__
        super().__init__(model, *args, default=MagicList, many=True, callback=callback, params=params, **kwargs)

class HasMixin(object):

    def set_ref(self, model=None, ref=None, attr=None):
        """Sets the 'ref' and 'attr' attributes. These attributes are used to defined parameters for
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
        self.ref = ref
        self.attr = attr

        if ref:
            self.ref = ref
        if not self.attr:
            self.attr = 'id'
        if not self.ref:
            self.ref = "{}_{}".format(inflection.underscore(model), self.attr)


class HasOne(HasMixin, One):
    def __init__(self, model, attr=None, ref=None, **kwargs):
        """
        HasOne initializer. Uses the "get_one_generic" callback and automatically
        assigns attribute as in the following:

        .. code-block:: python

            model="SampleType", attr="id" # equiv. to 'lambda self: self.sample_type_id.'

        :param model: model name of the target model
        :type model: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """
        self.set_ref(model=model, attr=attr, ref=ref)
        super().__init__(model, params=(lambda slf: getattr(slf, self.ref)), **kwargs)

    def __repr__(self):
        return "<HasOne (model={}, params=lambda self: self.{})>".format(self.nested, self.ref)


class HasManyThrough(HasMixin, Many):
    """A relationship using an intermediate association model"""

    def __init__(self, model, through, attr="id", ref=None, **kwargs):
        self.set_ref(model=model, attr=attr, ref=ref)

        # e.g. PlanAssociation >> plan_associations
        through_model_attr = inflection.pluralize(inflection.underscore(through))

        # e.g. {"id": x.operation_id for x in self.plan_associations
        params = lambda slf: {attr: [getattr(x, self.ref
                                             ) for x in getattr(slf, through_model_attr)]}
        super().__init__(model, params=params, **kwargs)


class HasMany(HasMixin, Many):
    def __init__(self, model, ref_model=None, attr=None, ref=None, **kwargs):
        """
        HasOne initializer. Uses the "get_one_generic" callback and automatically
        assigns attribute as in the following:

        .. code-block:: python

            model="SampleType", attr="id" # equiv. to  'lambda self: {sample_type_id: self.id}'

        :param model: model name of the target model
        :type model: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """

        self.set_ref(model=ref_model, attr=attr, ref=ref)
        params = lambda slf: {self.ref: getattr(slf, self.attr)}
        super().__init__(model, params=params, **kwargs)


# TODO: document hasmanygeneric
class HasManyGeneric(HasMany):
    def __init__(self, model, **kwargs):
        super().__init__(model, ref="parent_id", attr="id", **kwargs)
