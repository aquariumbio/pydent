"""
Aquarium model baseclass

This module contains the base classes for Trident models.
Trident models load from JSON and dump to JSON.
This is accomplished by adding the ``@add_schema`` decorator to classes inherited
by the Base class.
Using ``@add_schema`` dynamically creates a model schema that handles dumping and
loading.

Features of Trident models:

    load - models can be loaded from JSON data. Hierarchical JSON is loaded
    intelligently.

.. code-block:: python

    Sample.load({"name": "MyPrimer", "sample_type": {"name": "Primer", ...} })
    # => <Sample(name="MyPrimer", sample_type=<SampleType(name="Primer")>)>

dump - models can be dumped to JSON. Dependent models and relationships can be
       dumped as well.

.. code-block:: python

    s.dump(include=("sample_type"))

relationships - models relationships are stored

.. code-block:: python

    s = Sample.load(
        {"name": "MyPrimer",
        "sample_type_id": 1}
    )

    primer_type = s.sample_type

"""

from pydent.exceptions import TridentModelNotFoundError, AquariumModelError
from pydent.marshaller import MarshallerBase
from inflection import underscore


class ModelRegistry(type):
    """Stores a list of models that can be accessed by name."""
    models = {}

    def __init__(cls, name, bases, selfdict):
        """Saves model to the registry"""
        super().__init__(name, bases, selfdict)
        if not name == "ModelBase":
            ModelRegistry.models[name] = cls

    @staticmethod
    def get_model(model_name):
        """Gets model by model_name"""
        if model_name not in ModelRegistry.models:
            raise TridentModelNotFoundError(
                "Model \"{}\" not found in ModelRegistry.".format(model_name))
        else:
            return ModelRegistry.models[model_name]

    def __getattr__(cls, item):
        """
        Special warning for attribute errors.
        Its likely that user may have wanted to use a model interface instead of
        the Base class.
        """
        raise AttributeError("'{0}' has no attribute '{1}'. Method may be a ModelInterface method."
                             " Did you mean '<yoursession>.{0}.{1}'?"
                             .format(cls.__name__, item))


class ModelBase(MarshallerBase, metaclass=ModelRegistry):
    """
    Base class for Aquarium models.
    Subclass of :class:`pydent.marshaller.MarshallerBase`

    - creates instances from JSON using `load`
    - contains a reference to the :class:`pydent.session.aqsession.AqSession`
      instance that loaded this model
    """

    _global_record_id = 0

    def __init__(self, **model_args):
        self._session = None
        self._rid = None
        self._new_record_id()
        model_args['rid'] = self.rid
        vars(self).update(model_args)
        data = {k: v for k, v in model_args.items() if not k == '_session'}
        self._track_data(data)

    def _new_record_id(self):
        self._rid = ModelBase.new_record_id()

    @staticmethod
    def new_record_id():
        oid = ModelBase._global_record_id
        ModelBase._global_record_id += 1
        return oid

    @property
    def rid(self):
        return self._rid

    def _track_data(self, data):
        if self.model_schema:
            schema = self.model_schema()
            schema.load_missing(data.keys())
            schema.save_extra_fields(self)
            schema.validate(data)

    def append_to_many(self, name, model):
        """
        Appends a model to the many relationship

        :param name: name of the relationship or attribute
        :type name: str
        :param model: model to append
        :type model: ModelBase
        :return: None
        :rtype: None
        """
        if name in self.relationships:
            field = self.relationships[name]
            if not model.__class__.__name__ == field.model:
                raise AquariumModelError("Cannot 'append_to_many.' Model must be a '{}' but found a '{}'".format(
                    field.model, model.__class__.__name__))
            if field.many:
                val = getattr(self, name)
                if val is None:
                    val = []
                setattr(self, name, val)
                val.append(model)

    def set_model_attribute(self, model, attr="id"):
        model_name = underscore(model.__class__.__name__)
        if hasattr(model, attr):
            setattr(self, model_name + "_" + attr, getattr(model, attr))
        return model

    @classmethod
    def load(cls, *args, **kwargs):
        """Create a new model instance from loaded attributes"""
        inst = super().load(*args, **kwargs)
        if isinstance(inst, list):
            for _inst in inst:
                _inst._new_record_id()
        else:
            inst._new_record_id()
        return inst

    def dump(self, *args, **kwargs):
        d = super().dump(*args, **kwargs)
        if d is not None:
            d['rid'] = self._rid
        return d

    def reload(self, data):
        """
        Reload model attributes from new data

        :param data: data to update model instance
        :type data: dict
        :return: model instance
        :rtype: ModelBase
        """
        temp_model = self.__class__.load(data=data)
        temp_model.connect_to_session(self.session)
        vars(self).update(vars(temp_model))
        return self

    @property
    def session(self):
        """The connected session instance."""
        return self._session

    def connect_to_session(self, session):
        """Connect model instance to a session. Does nothing if session already exists."""
        if self._session is None:
            self._session = session

    def _check_for_session(self):
        """Raises error if model is not connected to a session"""
        if self.session is None:
            raise AttributeError("No AqSession instance found for '{}'. Use 'connect_to_session' "
                                 "to connect this model to a session".format(self.__class__.__name__))

    def no_getter(self, *_):
        """Callback that always returns None"""
        return None

    def create_interface(self):
        return self.interface(self.session)

    @classmethod
    def interface(cls, session):
        """Creates a model interface from this class and a session

        This method can be overridden in model definitions for special cases."""
        return session.model_interface(cls.__name__)

    @classmethod
    def find(cls, session, model_id):
        """Finds a model instance by its model_id"""
        interface = cls.interface(session)
        return interface.find(model_id)

    @classmethod
    def where(cls, session, params):
        """Finds a list of models by some parameters"""
        if params is None:
            return None
        interface = cls.interface(session)
        return interface.where(params)

    def find_callback(self, model_name, model_id):
        """Finds a model using the model interface and model_id. Used to find
        models in model relationships."""
        self._check_for_session()
        if model_id is None:
            return None
        model = ModelRegistry.get_model(model_name)
        return model.find(self.session, model_id)

    def where_callback(self, model_name, *args, **kwargs):
        """Finds models using a model interface and a set of parameters. Used to
        find models in model relationships."""
        self._check_for_session()
        query_arg = args[0]

        if isinstance(query_arg, dict):
            if len(query_arg) == 1 and list(query_arg.values())[0] is None:
                return None
            if None in query_arg.values():
                return None
        model = ModelRegistry.get_model(model_name)
        if kwargs is None:
            kwargs = {}
        return model.where(self.session, query_arg, *args[1:], **kwargs)

    # def patch(self, json_data):
    #     """Make a patch request to self using json_data. Reload model instance with new data"""
    #     result = self.create_interface().patch(self.id, json_data=json_data)
    #     self.reload(data=result)
    #     return self
    #
    # def patch_with_self(self, **kwargs):
    #     """Update changes to this model instance to Aquarium."""
    #     json_data = self.dump(**kwargs)
    #     return self.patch(json_data=json_data)

    def __getattribute__(self, name):
        """Override getattribute to automatically connect sessions"""
        res = super().__getattribute__(name)
        if isinstance(res, list) or isinstance(res, MarshallerBase):
            relationships = object.__getattribute__(
                self, "get_relationships")()
            if name in relationships:
                session = object.__getattribute__(self, 'session')
                if isinstance(res, list):
                    [m.connect_to_session(session) for m in res]
                else:
                    res.connect_to_session(session)
        return res
