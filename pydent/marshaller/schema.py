"""Model serialization/deserialization schema."""
import inspect
from typing import Type

from pydent.marshaller.descriptors import DataAccessor
from pydent.marshaller.exceptions import CallbackValidationError
from pydent.marshaller.exceptions import MultipleValidationError
from pydent.marshaller.exceptions import SchemaException
from pydent.marshaller.fields import Callback
from pydent.marshaller.fields import Field
from pydent.marshaller.registry import SchemaRegistry
from pydent.marshaller.utils import make_signature_str


class DynamicSchema(metaclass=SchemaRegistry):
    """A dynamically added schema.

    Should be added using '@add_schema` decorator.
    """

    ignore = ()
    fields = dict()

    @classmethod
    def _get_model_fields(cls):
        return cls.fields

    @classmethod
    def init_field_accessors(cls):
        """Initializes callback accessors.

        :return:
        :rtype:
        """
        for field_name, field in cls._get_model_fields().items():
            field.register(field_name, cls.model_class)

    @classmethod
    def init_data_accessors(cls, instance, data, add_extra=True):
        """Initializes data accessors.

        :param instance:
        :type instance:
        :param data:
        :type data:
        :param add_extra:
        :return:
        :rtype:
        """
        if cls.model_class is not instance.__class__:
            raise SchemaException("Instance and model class are different")
        for k, v in dict(data).items():
            if k in cls.ignore:
                data.pop(k, None)
                continue
            if not add_extra and k not in cls.model_class.fields:
                raise AttributeError(
                    "Expected field missing. Cannot initialize accessor for '{}' for "
                    "'{}' because it is not a field."
                    " It may be missing from the 'field' dictionary.".format(
                        k, cls.model_class
                    )
                )
            if k not in cls.model_class.__dict__:
                setattr(cls.model_class, k, DataAccessor(k, cls.model_class._data_key))
            try:
                setattr(instance, k, v)
            except AttributeError as e:
                raise e

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
        for rname, callback_field in cls.grouped_fields[Callback.__name__].items():
            callback_func = callback_field.callback
            if callback_func is None:
                missing_callbacks.append(
                    "Callback for {model}.{name} cannot be None".format(
                        model=model_class.__name__, name=rname
                    )
                )
                continue
            error_prefix = "Callback '{callback}' for relationship '{model}.{name}'".format(
                callback=callback_func, model=model_class.__name__, name=rname
            )
            if not callable(callback_func) and not hasattr(model_class, callback_func):
                if callback_func not in missing_callbacks:
                    missing_callbacks.append(error_prefix + " is missing.")
            else:
                args_to_send = list(callback_field.callback_args)
                kwargs_to_send = dict(callback_field.callback_kwargs)
                if isinstance(callback_func, str):
                    callback_func = getattr(model_class, callback_func)
                    args_to_send = ["self"] + args_to_send
                if not callable(callback_func):
                    not_callable.append(error_prefix + " is not callable.")
                else:
                    signature = inspect.getfullargspec(callback_func)
                    expected_args = signature.args
                    expected_kwargs = {}
                    if signature.defaults:
                        default_args = expected_args[-len(signature.defaults) :]
                        expected_args = expected_args[: -len(signature.defaults)]
                        expected_kwargs = dict(zip(default_args, signature.defaults))

                    if (
                        len(expected_args) != len(args_to_send)
                        and not signature.varargs
                    ):
                        wrong_signature.append(
                            error_prefix
                            + " expects arguments {receive_args} but would receive "
                            "arguments {sent_args}.".format(
                                receive_args=make_signature_str(
                                    expected_args, expected_kwargs
                                ),
                                sent_args=make_signature_str(
                                    list(args_to_send), kwargs_to_send
                                ),
                            )
                        )
                    else:
                        for k in kwargs_to_send:
                            invalid_keys = []
                            if k not in expected_kwargs and not signature.varkw:
                                invalid_keys.append(k)
                            if invalid_keys:
                                wrong_signature.append(
                                    error_prefix
                                    + " does not recognize named key(s) {invalid_keys} "
                                    "from signature {receive_args}.".format(
                                        invalid_keys=", ".join(
                                            ['"{}"'.format(key) for key in invalid_keys]
                                        ),
                                        receive_args=make_signature_str(
                                            expected_args, expected_kwargs
                                        ),
                                    )
                                )
                                wrong_signature.append(callback_func)

        with MultipleValidationError("") as e:
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
    def register(cls, model_class: Type):
        """Registers the schema to a model class. Saves the schema class to the
        class attribute.

        :param model_class: a model class
        :type model_class: type
        :return: None
        :rtype: None
        """
        setattr(model_class, "_model_schema", cls)

        schema_fields = {}
        ignored_fields = {}
        fields_key = model_class._fields_key
        if hasattr(model_class, fields_key):
            model_fields = getattr(model_class, fields_key)

            ignore = model_fields.pop("ignore", ())
            if isinstance(ignore, str):
                ignore = (ignore,)
            cls.ignore = ignore

            for field_name, field in model_fields.items():
                if field_name in cls.ignore:
                    ignored_fields[field_name] = field
                elif issubclass(type(field), Field):
                    if field.data_key is None:
                        field.data_key = field_name
                    if issubclass(type(field), Field):
                        schema_fields[field_name] = field
            setattr(model_class, fields_key, schema_fields)
            setattr(model_class, "_ignored_fields", ignored_fields)
        setattr(cls, "_fields", schema_fields)
        setattr(cls, "_ignored_fields", ignored_fields)
        cls.init_field_accessors()
        cls.validate_callbacks()
