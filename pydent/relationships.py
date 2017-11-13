import inflection
from pydent.marshaller import Relation


class One(Relation):
    """Defines a single relationship with another model."""

    def __init__(self, model, *args, attr=None, **kwargs):
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
        super().__init__(model, *args, callback="find",
                         params=(lambda self: getattr(self, attr),), **kwargs)


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
        super().__init__(model, *args, many=True, callback="where", params=params)


class HasOne(One):

    def __init__(self, model, attr="id"):
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
        iden = "{}_{}".format(underscore, attr)
        super().__init__(model, param=(lambda self: getattr(self, iden)))


class HasMany(Many):

    def __init__(self, model, ref_model, attr="id"):
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

        # {"id": self.id}
        params = lambda self: {iden: getattr(self, attr)}
        super().__init__(model, params=params)
