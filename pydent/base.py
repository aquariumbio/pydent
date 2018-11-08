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

from pydent.exceptions import AquariumModelError
from pydent.marshaller import SchemaModel, ModelRegistry
from pydent.marshaller import fields
from inflection import underscore
import itertools


class ModelBase(SchemaModel):
    """
    Base class for Aquarium models.
    Subclass of :class:`pydent.marshaller.MarshallerBase`

    - creates instances from JSON using `load`
    - contains a reference to the :class:`pydent.session.aqsession.AqSession`
      instance that loaded this model
    """
    PRIMARY_KEY = 'id'
    GLOBAL_KEY = 'rid'
    counter = itertools.count()

    def __init__(self, **data):
        super().__init__(data)
        self._rid = next(self.counter)
        self.add_data({"rid": self._rid, "id": data.get('id', None)})
        self._session = None

    @classmethod
    def _set_data(cls, data):
        instance = cls.__new__(cls)
        cls.__init__(instance)
        ModelBase.__init__(instance, **data)
        return instance
    # def __init__(self, **kwargs):
    #     self.add_data(kwargs)

    # def setup(self):
    #     self._session = None
    #
    # @classmethod
    # def model_factory(cls, data):
    #     instance = cls._set_data(data)

    # def __init__(self, **model_args):
    #     model_args.update({"rid": self._rid})
    #     super().__init__(model_args)

    @property
    def rid(self):
        return self._rid

    @property
    def _primary_key(self):
        """Returns the primary key (e.g. 'id') or the rid if id does not exist or is None"""
        if hasattr(self, ModelBase.PRIMARY_KEY):
            pk = getattr(self, ModelBase.PRIMARY_KEY)
            if pk:
                return pk
        return 'r{}'.format(self.rid)

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
        if name in self.get_relationships():
            field = self.get_relationships()[name]
            if not model.__class__.__name__ == field.nested:
                raise AquariumModelError("Cannot 'append_to_many.' Model must be a '{}' but found a '{}'".format(
                    field.model, model.__class__.__name__))
            if field.many:
                val = getattr(self, name)
                if val is None:
                    val = []
                    setattr(self, name, val)
                getattr(self, name).append(model)
        return self

    def set_model_attribute(self, model, attr=None):
        if attr is None:
            attr = ModelBase.PRIMARY_KEY
        model_name = underscore(model.__class__.__name__)
        if hasattr(model, attr):
            setattr(self, model_name + "_" + attr, getattr(model, attr))
        return model

    @classmethod
    def load(cls, data):
        """Create a new model instance from loaded attributes"""
        if isinstance(data, list):
            models = []
            for d in data:
                model = cls._set_data(d)
                models.append(model)
            return models
        else:
            model = cls._set_data(data)
        return model

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

    @classmethod
    def get_relationships(cls):
        return cls._model_schema.grouped_fields[fields.Relationship.__name__]

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

    @classmethod
    def one(cls, session, query, **kwargs):
        interface = cls.interface(session)
        query = dict(query)
        query.update(kwargs)
        return interface.one(**query)

    def one_callback(self, model_name, *args, **kwargs):
        self._check_for_session()
        model = ModelRegistry.get_model(model_name)
        return model.one(self.session, *args, **kwargs)

    def find_callback(self, model_name, model_id):
        """Finds a model using the model interface and model_id. Used to find
        models in model relationships."""
        self._check_for_session()
        if model_id is None:
            return None
        model = ModelRegistry.get_model(model_name)
        self.session._log_to_aqhttp(
            "CALLBACK '{clsname}(rid={rid})' made a FIND request for '{model}'".format(
                clsname=self.__class__.__name__,
                rid=self.rid,
                model=model_name))
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
        self.session._log_to_aqhttp("CALLBACK '{clsname}(rid={rid})' made a WHERE request for '{model}'".format(
            clsname=self.__class__.__name__,
            rid=self.rid,
            model=model_name)
        )
        return model.where(self.session, query_arg, *args[1:], **kwargs)

    def print(self):
        data = self.dump()
        relationships = self.get_relationships()
        data.update(relationships)
        print(data)

    def __str__(self):
        return self._to_str('id', 'rid')

    def _to_str(self, *attributes):
        return "<{} {}>".format(self.__class__.__name__, ' '.join([
            "{}={}".format(k, self._get_data().get(k, None)) for k in attributes
        ]))

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

    # def __getattribute__(self, name):
    #     """Override getattribute to automatically connect sessions"""
    #     res = super().__getattribute__(name)
    #     if isinstance(res, list) or isinstance(res, SchemaModel):
    #         relationships = object.__getattribute__(
    #             self, "get_relationships")()
    #         if name in relationships:
    #             session = object.__getattribute__(self, 'session')
    #             if isinstance(res, list):
    #                 [m.connect_to_session(session) for m in res]
    #             else:
    #                 res.connect_to_session(session)
    #     return res
