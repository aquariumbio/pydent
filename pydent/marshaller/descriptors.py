"""Data descriptors that provide special behaviors when attributes are
accessed."""
from enum import auto
from enum import Enum

from .exceptions import MarshallerBaseException


class MarshallingAttributeAccessError(MarshallerBaseException):
    """Generic error that arises from while accessing an attribute."""


class Placeholders(Enum):
    """Accessor placeholders.

    Special behaviors can occur when the descriptor returns a value in
    the Placeholder class. For example, when the `Placeholders.CALLBACK`
    value is returned and cache=True, this indicates that the callback
    function needs to be called and the result cached.
    """

    DATA = auto()  #: DATA accessor holder.
    MARSHALL = auto()  #: MARSHALL accessor holder.
    CALLBACK = auto()  #: CALLBACK accessor holder.
    DEFAULT = auto()  #: DEFAULT accessor holder.


class DataAccessor:
    """A descriptor that will dynamically access an instance's dictionary named
    by the `accessor` key. If the key is not in the dictionary or the value
    received from the dictionary is a :class:`Placeholders.DATA` enumerator, an
    AttributeError is raised.

    **Usage**:

    This may be used to assign dynamic properties to a class method as in
    the example below, or subclasses of the DataAccessor can be created
    to create 'hooks' when the descriptor is accessed, set, or delete.

    .. code-block::

        model_class.x = DataAccessor('x')
        model_class.y = DataAccessor('y')
        instance = model_class()

        instance.data # {'x': Placeholders.DATA, 'y': Placeholders.DATA}

        # accessing the default values
        try:
            instance.x
        except AttributeError:
            print("x being tracked but is not set")

        # setting and accessing a value
        instance.x = 5
        instance.data = {'x': 5, 'y': Placeholders.DATA}
        instance.x  # returns 5

        # raising AttributeError
        try:
            instance.y
        except AttributeError:
            print("y is not set")

        # setting the value
        instance.y = 10
        assert instance.data == {'x': 5, 'y': 10}
        assert instance.y == 10

        # deleting the value
        del instance.y
        assert instance.data == {'x': 5, 'y': Placeholders.DATA}
        try:
            instance.y
        except AttributeError:
            print("y is not set")
    """

    __slots__ = ["name", "accessor", "default"]
    HOLDER = Placeholders.DATA

    def __init__(self, name, accessor=None, default=HOLDER):
        self.name = name
        self.accessor = accessor
        if default is Placeholders.DEFAULT:
            default = self.HOLDER
        self.default = default
        if self.name == self.accessor:
            raise MarshallingAttributeAccessError(
                "Descriptor name '{}' cannot be accessor name '{}'".format(
                    self.name, self.accessor
                )
            )

    def get_val(self, obj):
        access_data = getattr(obj, self.accessor)
        return access_data.get(self.name, self.default)

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            raise AttributeError(
                "type object '{}' does not have attribute '{}'".format(
                    obj.__class__.__name__, self.name
                )
            )
        else:
            return val

    def __set__(self, obj, val):
        getattr(obj, self.accessor)[self.name] = val

    def __delete__(self, obj):
        getattr(obj, self.accessor)[self.name] = self.HOLDER


class MarshallingAccessor(DataAccessor):
    """A generic Marshalling descriptor."""

    __slots__ = ["name", "accessor", "field", "deserialized_accessor", "default"]
    HOLDER = Placeholders.MARSHALL

    def __init__(self, name, field, accessor, deserialized_accessor, default=HOLDER):
        super().__init__(name, accessor, default=default)
        self.deserialized_accessor = deserialized_accessor
        if self.accessor == self.deserialized_accessor:
            raise MarshallingAttributeAccessError(
                "Descriptor accessor '{}' cannot be deserialized accessor '{}'".format(
                    self.accessor, self.deserialized_accessor
                )
            )
        self.field = field

    def get_val(self, obj):
        try:
            return getattr(obj, self.deserialized_accessor).get(self.name, self.default)
        except AttributeError as e:
            raise e
        except Exception as e:
            raise MarshallingAttributeAccessError(
                "Error retrieving attribute '{}' from '{}' because:\n".format(
                    self.name, obj.__class__
                )
                + "{}: ".format(e.__class__.__name__)
                + str(e)
            ) from e

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            val = getattr(obj, self.accessor).get(self.name, self.HOLDER)
            if val is self.HOLDER:
                raise AttributeError(
                    "type object '{}' does not have attribute '{}'".format(
                        obj.__class__.__name__, self.name
                    )
                )
            else:
                return self.field.deserialize(obj, val)
        return val

    def __set__(self, obj, val):
        try:
            deserialized = self.field.deserialize(obj, val)
            serialized = self.field.serialize(obj, deserialized)
            getattr(obj, self.deserialized_accessor)[self.name] = deserialized
            getattr(obj, self.accessor)[self.name] = serialized
        except Exception as e:
            from traceback import format_tb

            print("__set__ traceback:")
            print("\n".join(format_tb(e.__traceback__)))
            raise MarshallingAttributeAccessError(
                "can't set attribute '{}' for '{}' to '{}' due to:\n{}. "
                "See the traceback printed above".format(self.name, obj, val, str(e))
            ) from e

    def __delete__(self, obj):
        del getattr(obj, self.accessor)[self.name]
        del getattr(obj, self.deserialized_accessor)[self.name]


class CallbackAccessor(MarshallingAccessor):
    """A descriptor that uses a registered :class:`marshaller.fields.Callback`
    to dynamically access the value of a callback by sending the instance to
    the callback field's `fullfill` method if the descriptor is not yet set.

    If the descriptor is already set, return that value. Deleting the
    descriptor sets the value to the default
    :class:`Placeholders.CALLBACK`, which will attempt to `fullfill` the
    descriptor once accessed.
    """

    __slots__ = ["name", "accessor", "field", "deserialized_accessor", "default"]
    HOLDER = Placeholders.CALLBACK

    def __init__(self, name, field, accessor, deserialized_accessor, default=HOLDER):
        super().__init__(name, field, accessor, deserialized_accessor, default=default)

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            val = self.field.fullfill(obj)
        return val

    def __set__(self, obj, val):
        getattr(obj, self.deserialized_accessor)[self.name] = val
        getattr(obj, self.accessor)[self.name] = self.field.serialize(obj, val)


class RelationshipAccessor(CallbackAccessor):
    """The descriptor for a :class:`pydent.marshaller.fields.Relationship`
    field."""

    def __set__(self, obj, val):
        deserialized = self.field.deserialize(obj, val)
        serialized = self.field.serialize(obj, deserialized)
        getattr(obj, self.deserialized_accessor)[self.name] = deserialized
        getattr(obj, self.accessor)[self.name] = serialized
