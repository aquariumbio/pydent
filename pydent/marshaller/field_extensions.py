"""
Module containing custom :class:`marshmallow.fields`.
"""

import json
from marshmallow import fields, ValidationError


class JSON(fields.Field):
    """A custom JSON field"""

    def _serialize(self, value, attr, obj):
        if value is None:
            return ''
        try:
            return json.dumps(value)
        except TypeError as error:
            raise ValidationError(error)

    def _deserialize(self, value, attr, data):
        if value is None:
            return ''
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError as error:
            raise ValidationError(error)

    default_error_message = {
        'invalid': 'field was unable to be parsed as a JSON'
    }


class Relation(fields.Nested):
    """
    Defines a nested relationship with another model.

    Uses "callback" with "params" to find models.
    Callback is applied to the model that is fullfilling this relation.
    Params may be lambdas of the form "lambda self: <do something with self>"
    which passes in the model instance.
    """

    def __init__(self, model, callback, params, *args, allow_none=True, **kwargs):
        """
        Relation initializer.

        :param model: target model
        :type model: basestring
        :param args: positional parameters
        :type args:
        :param callback: function to use in Base to find model
        :type callback: basestring or callable
        :param params: tuple or list of variables (or callables) to use to
                       search for the model. If param is a callable, the model
                       instance will be passed in.
        :type params: tuple or list
        :param kwargs: rest of the parameters
        :type kwargs:
        """
        super().__init__(model, *args, allow_none=allow_none, **kwargs)
        self.callback = callback
        # force params to be an iterable
        if not isinstance(params, (list, tuple)):
            params = (params,)
        self.params = params

    @property
    def model(self):
        return self.nested

    def _serialize(self, nested_obj, attr, obj):
        dumped = None

        def dump(nobj):
            if hasattr(nobj, 'dump'):
                nobj = nobj.dump()
            return nobj

        if nested_obj:
            if isinstance(nested_obj, list):
                dumped = []
                for model in nested_obj:
                    xdumped = None
                    if model is not None:
                        xdumped = dump(model)
                    dumped.append(xdumped)
            else:
                dumped = dump(nested_obj)
        return dumped

    def __repr__(self):
        return "<{} (model={}, callback={}, params={})>".format(
            self.__class__.__name__,
            self.nested, self.callback, self.params)


fields.Relation = Relation
fields.JSON = JSON
