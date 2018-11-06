import inspect

from pydent.marshaller.registry import SchemaRegistry
from pydent.marshaller.exceptions import MultipleValidationError, CallbackValidationError
from pydent.marshaller.descriptors import DataAccessor
from pydent.marshaller.fields import Field, Callback


class DynamicSchema(metaclass=SchemaRegistry):

    model_class = None

    @classmethod
    def init_field_accessors(cls):
        """Initializes callback accessors.

        :return:
        :rtype:
        """
        for field_name, field in cls.fields.items():
            field.register(field_name, cls.model_class)

    # TODO: is 'update' the best way to handle setting the values?
    @classmethod
    def init_data_accessors(cls, instance, data):
        """Initializes data accessors.

        :param instance:
        :type instance:
        :param data:
        :type data:
        :return:
        :rtype:
        """
        for k, v in data.items():
            if k not in cls.model_class.__dict__:
                setattr(cls.model_class, k, DataAccessor(k, cls.model_class._data_key))
            setattr(instance, k, v)

    @classmethod
    def validate_callbacks(cls):
        """Validates expected callback signature found in any callback in the
        registered model fields.

        :return: None
        :rtype: None
        :raises: ModelValidationError
        """
        missing_callbacks = []
        not_callable = []
        wrong_signature = []
        model_class = cls.model_class
        for rname, callback_field in cls.grouped_fields[Callback.__name__]:
            callback_func = callback_field.callback
            if callback_func is None:
                missing_callbacks.append("Callback for {model}.{name} cannot be None".format(
                    model=model_class.__name__, name=rname))
                continue
            error_prefix = "Callback '{callback}' for relationship '{model}.{name}'".format(
                callback=callback_func, model=model_class.__name__, name=rname)
            if not callable(callback_func) and not hasattr(model_class, callback_func):
                if callback_func not in missing_callbacks:
                    missing_callbacks.append(error_prefix + " is missing")
            else:
                args_to_send = list(callback_field.callback_args)
                kwargs_to_send = dict(callback_field.callback_kwargs)
                if isinstance(callback_func, str):
                    callback_func = getattr(model_class, callback_func)
                    args_to_send = ['self'] + args_to_send
                if not callable(callback_func):
                    not_callable.append(error_prefix + " is not callable")
                else:
                    signature = inspect.getfullargspec(callback_func)
                    expected_args = signature.args
                    expected_kwargs = {}
                    if signature.defaults:
                        default_args = expected_args[-len(signature.defaults):]
                        expected_args = expected_args[:-len(signature.defaults)]
                        expected_kwargs = dict(zip(default_args, signature.defaults))

                    make_signature = lambda _args, _kwargs: "({}, {})".format(
                        ', '.join([str(_a) for _a in _args]),
                        ', '.join(['{}={}'.format(name, val) for name, val in _kwargs.items()])
                    )

                    if len(expected_args) != len(args_to_send) and not signature.varargs:
                        wrong_signature.append(
                            error_prefix +
                            " expects arguments {receive_args} but would receive arguments {sent_args}".format(
                                receive_args=make_signature(expected_args, expected_kwargs),
                                sent_args=make_signature(list(args_to_send), kwargs_to_send)))
                    else:
                        for k in kwargs_to_send:
                            invalid_keys = []
                            if k not in expected_kwargs:
                                invalid_keys.append(k)
                            if invalid_keys:
                                wrong_signature.append(
                                    error_prefix +
                                    " does not recognize named key(s) {invalid_keys} from signature {receive_args}".
                                    format(
                                        invalid_keys=', '.join(['"{}"'.format(key) for key in invalid_keys]),
                                        receive_args=make_signature(expected_args, expected_kwargs),
                                    ))
                                wrong_signature.append(callback_func)

        with MultipleValidationError('') as e:
            if missing_callbacks:
                for w in missing_callbacks:
                    e.r(CallbackValidationError(w))
            if not_callable:
                for w in not_callable:
                    e.r(CallbackValidationError(w))
            if wrong_signature:
                for w in wrong_signature:
                    e.r(CallbackValidationError(w))

    @classmethod
    def register(cls, model_class):
        """Registers the schema to a model class. Saves the schema class to the
        class attribute.

        :param model_class: a model class
        :type model_class: type
        :return: None
        :rtype: None
        """
        setattr(model_class, "_model_schema", cls)
        setattr(cls, "_model_class", model_class)

        fields = {}
        if hasattr(model_class, model_class._fields_key):
            for field_name, field in getattr(model_class, model_class._fields_key).items():
                if issubclass(type(field), Field):
                    if field.data_key is None:
                        field.data_key = field_name
                    if issubclass(type(field), Field):
                        fields[field_name] = field
        setattr(cls, "_fields", fields)
        cls.init_field_accessors()
        cls.validate_callbacks()
