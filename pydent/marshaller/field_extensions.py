"""
Module containing custom :class:`marshmallow.fields`.
"""

import json
from marshmallow import fields, ValidationError


class JSON(fields.Field):
    """A custom JSON field"""

    def __init__(self, *args, strict=True, **kwargs):
        """
        Serializes and deserializes JSON

        :param args: params
        :param strict: if True, returns error if value is not strictly a JSON
        :param kwargs: key-value params
        """
        super().__init__(*args, **kwargs)
        self.strict = strict

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        try:
            return json.dumps(value)
        except TypeError as error:
            if self.strict:
                raise ValidationError(error)
            else:
                return value

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        elif value == '':
            return None
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError as error:
            if self.strict:
                raise ValidationError(error)
            else:
                return value

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

    def __init__(self, model, callback, callback_args, *field_args, allow_none=True, callback_kwargs=None, **field_kwargs):
        """
        Relation initializer.

        :param model: target model
        :type model: basestring
        :param field_args: positional parameters
        :type field_args:
        :param callback: function to use in Base to find model
        :type callback: basestring or callable
        :param callback_args: tuple or list of variables (or callables) to use to
                       search for the model. If param is a callable, the model
                       instance will be passed in.
        :type callback_args: tuple or list
        :param field_kwargs: rest of the parameters
        :type field_kwargs:
        """
        super().__init__(model, *field_args, allow_none=allow_none, **field_kwargs)
        self.callback = callback
        # force params to be an iterable
        if not isinstance(callback_args, (list, tuple)):
            callback_args = (callback_args,)
        self.callback_args = callback_args
        if callback_kwargs is None:
            callback_kwargs = {}
        self.callback_kwargs = callback_kwargs

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
            self.nested, self.callback, self.callback_args)


fields.Relation = Relation
fields.JSON = JSON
