"""Nested model relationships for Aquarium models.
"""

import inflection

from pydent.base import ModelBase
from pydent.marshaller import fields
from pydent.marshaller.exceptions import MarshallerRelationshipError


class One(fields.Relation):
    """
    Defines a single relationship with another model.
    Subclass of :class:`pydent.marshaller.Relation`.
    """

    def __init__(self, model, *args, callback=None, callback_args=None, callback_kwargs=None, **kwargs):
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
        super().__init__(model, *args, callback=callback, callback_args=callback_args, callback_kwargs=callback_kwargs, **kwargs)


class Many(fields.Relation):
    """
    Defines a many relationship with another model.
    Subclass of :class:`pydent.marshaller.Relation`.
    """

    def __init__(self, model, *args, callback=None, callback_args=None, callback_kwargs=None, **kwargs):
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
        super().__init__(model, *args, default=list,
                         many=True, callback=callback, callback_args=callback_args, callback_kwargs=callback_kwargs, **kwargs)


class HasMixin:
    """
    Mixin for adding the 'set_ref' method. 'set_ref' builds a 'ref' and 'attr'
    attributes
    """

    def set_ref(self, model=None, ref=None, attr=None):
        """
        Sets the 'ref' and 'attr' attributes. These attributes are used to
        defined parameters for
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

        if not self.attr:
            self.attr = 'id'
        if ref:
            self.ref = ref
        else:
            if not self.attr:
                raise MarshallerRelationshipError(
                    "'attr' is None. Relationship '{}' needs an 'attr' and 'model' parameters".format(self.__class__))
            if not model:
                raise MarshallerRelationshipError(
                    "'model' is None. Relationship '{}' needs an 'attr' and 'model' parameters".format(self.__class__))
            self.ref = "{}_{}".format(inflection.underscore(model), self.attr)


class HasOne(HasMixin, One):
    def __init__(self, model, attr=None, ref=None, callback_kwargs=None, **kwargs):
        """
        HasOne initializer. Uses the "get_one_generic" callback and
        automatically assigns attribute as in the following:

        .. code-block:: python

            model="SampleType", attr="id" # equiv. to 'lambda self: self.sample_type_id.'

        :param model: model name of the target model
        :type model: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """
        self.set_ref(model=model, attr=attr, ref=ref)
        super().__init__(model, callback_args=(lambda slf: getattr(slf, self.ref)), callback_kwargs=callback_kwargs, **kwargs)

    def __repr__(self):
        return "<HasOne (model={}, callback_args=lambda self: self.{})>".format(self.model, self.ref)


class HasManyThrough(HasMixin, Many):
    """
    A relationship using an intermediate association model.
    Establishes a Many-to-Many relationship with another model
    """

    def __init__(self, model, through, attr="id", ref=None, callback_kwargs=None, **kwargs):
        self.set_ref(model=model, attr=attr, ref=ref)

        # e.g. PlanAssociation >> plan_associations
        through_model_attr = inflection.pluralize(
            inflection.underscore(through))

        # e.g. {"id": x.operation_id for x in self.plan_associations
        def callback_args(slf):
            through_model = getattr(slf, through_model_attr)
            if through_model is None:
                return None
            return {attr: [getattr(x, self.ref) for x in getattr(slf, through_model_attr)]}
        super().__init__(model, callback_args=callback_args, callback_kwargs=callback_kwargs, **kwargs)


class HasMany(HasMixin, Many):
    """
    A relationship that establishes a One-to-Many relationship with another model.
    """

    def __init__(self, model, ref_model=None, attr=None, ref=None, callback_kwargs=None, **kwargs):
        """
        HasMany relationship initializer

        :param model: Model class name for this relationship
        :type model: str
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
            raise MarshallerRelationshipError(
                msg.format(self.__class__.__name__))
        self.set_ref(model=ref_model, attr=attr, ref=ref)

        def callback_args(slf): return {self.ref: getattr(slf, self.attr)}
        super().__init__(model, callback_args=callback_args, callback_kwargs=callback_kwargs, **kwargs)


class HasManyGeneric(HasMany):
    """
    Establishes a One-to-Many relationship using 'parent_id' as the attribute
    to find other models.
    """

    def __init__(self, model, callback_kwargs=None, **kwargs):
        super().__init__(model, ref="parent_id", attr="id", callback_kwargs=callback_kwargs, **kwargs)
