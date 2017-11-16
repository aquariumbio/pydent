import inflection
from pydent.marshaller import Relation


# TODO: Is this ravioli? Too many different types of relationships?

class One(Relation):
    """Defines a single relationship with another model."""

    def __init__(self, model, *args, params=None, **kwargs):
        """
        One initializer. Uses "get_one_generic" callback.

        :param model: target model
        :type model: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        if params is None:
            iden = "{}_id".format(inflection.underscore(model))
            params = lambda slf: getattr(slf, iden)
        super().__init__(model, *args, callback="find", params=params, **kwargs)


class Many(Relation):
    """Defines a many relationship with another model."""

    def __init__(self, model, *args, params=None, **kwargs):
        """
        Many initializer. Uses "get_many_generic" callback.

        :param model: target model
        :type model: basestring
        :param args: other args for fields.Nested relationship
        :type args: ...
        :param attr: attribute to use to find model
        :type attr: basestring
        :param kwargs: other kwargs for fields.Nested relationship
        :type kwargs: ...
        """
        super().__init__(model, *args, many=True, callback="where", params=params, **kwargs)


class HasOne(One):
    def __init__(self, model, attr="id", **kwargs):
        """
        HasOne initializer. Uses the "get_one_generic" callback and automatically
        assigns attribute as in the following:

            model="SampleType", attr="id" >> lambda self: self.sample_type_id.

        :param model: model name of the target model
        :type model: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """
        underscore = inflection.underscore(model)
        self.iden = "{}_{}".format(underscore, attr)
        super().__init__(model, params=(lambda slf: getattr(slf, self.iden)), **kwargs)

    def __repr__(self):
        return "<HasOne (model={}, params=lambda self: self.{})>".format(self.nested, self.iden)


class HasManyThrough(Many):
    """A relationship using an intermediate association model"""

    def __init__(self, model, through, attr="id", **kwargs):
        # e.g. Operation >> operation_id
        iden = "{}_{}".format(inflection.underscore(model), attr)

        # e.g. PlanAssociation >> plan_associations
        through_model_attr = inflection.pluralize(inflection.underscore(through))

        # e.g. {"id": x.operation_id for x in self.plan_associations
        params = lambda slf: {attr: [getattr(x, iden) for x in getattr(slf, through_model_attr)]}
        super().__init__(model, params=params, **kwargs)


class HasMany(Many):
    def __init__(self, model, ref_model, attr="id", through=None, **kwargs):
        """
        HasOne initializer. Uses the "get_one_generic" callback and automatically
        assigns attribute as in the following:

            model="SampleType", attr="id" >> lambda self: {sample_type_id: self.id}

        :param model: model name of the target model
        :type model: basestring
        :param attr: attribute to append underscored model name
        :type attr: basestring
        """

        # "SampleType" >>> "sample_type_id"
        underscore = inflection.underscore(ref_model)
        iden = "{}_{}".format(underscore, attr)

        params = ()
        if through:
            # e.g.
            through_model_attr = inflection.pluralize(inflection.underscore(through))
            params = lambda slf: {attr: [getattr(x, iden) for x in getattr(slf, through_model_attr)]}
        else:
            params = lambda slf: {iden: getattr(slf, attr)}
        super().__init__(model, params=params, **kwargs)


class HasManyGeneric(Many):
    def __init__(self, model):
        super().__init__(model, params=lambda slf: {"parent_id": slf.id})
