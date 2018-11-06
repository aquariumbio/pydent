from enum import Enum, auto


class Placeholders(Enum):
    DATA = auto()
    MARSHALL = auto()
    CALLBACK = auto()


class DataAccessor(object):
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

    __slots__ = ['name', 'accessor']
    HOLDER = Placeholders.DATA

    def __init__(self, name, accessor=None):
        self.name = name
        self.accessor = accessor

    def get_val(self, obj):
        return getattr(obj, self.accessor).get(self.name, self.HOLDER)

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            raise AttributeError("type object '{}' does not have attribute '{}'".format(
                obj.__class__.__name__, self.name))
        else:
            return val

    def __set__(self, obj, val):
        getattr(obj, self.accessor)[self.name] = val

    def __delete__(self, obj):
        getattr(obj, self.accessor)[self.name] = self.HOLDER


class MarshallingAccessor(DataAccessor):

    __slots__ = ['name', 'accessor', 'field', 'deserialized_accessor']
    HOLDER = Placeholders.MARSHALL

    def __init__(self, name, field, accessor, deserialized_accessor):
        super().__init__(name, accessor)
        self.deserialized_accessor = deserialized_accessor
        self.field = field

    def get_val(self, obj):
        return getattr(obj, self.deserialized_accessor).get(self.name, self.HOLDER)

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            val = getattr(obj, self.accessor).get(self.name, self.HOLDER)
            if val is self.HOLDER:
                raise AttributeError("type object '{}' does not have attribute '{}'".format(
                    obj.__class__.__name__, self.name))
            else:
                return self.field.deserialize(obj, val)
        return val

    def __set__(self, obj, val):
        deserialized = self.field.deserialize(obj, val)
        serialized = self.field.serialize(obj, deserialized)
        getattr(obj, self.accessor)[self.name] = serialized
        getattr(obj, self.deserialized_accessor)[self.name] = deserialized

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

    __slots__ = ['name', 'accessor', 'field', 'deserialized_accessor']
    HOLDER = Placeholders.CALLBACK

    def __get__(self, obj, objtype):
        val = self.get_val(obj)
        if val is self.HOLDER:
            return self.field.fullfill(obj)
        else:
            return val

    def __set__(self, obj, val):
        getattr(obj, self.deserialized_accessor)[self.name] = val
        getattr(obj, self.accessor)[self.name] = self.field.serialize(obj, val)
