"""
Aquarium model baseclass

This module contains the base classes for Trident models.
Trident models load from JSON and dump to JSON.
This is accomplished by adding the ``@add_schema`` decorator to classes
inherited by the Base class.
Using ``@add_schema`` dynamically creates a model schema that handles dumping
and loading.

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

from pydent.exceptions import AquariumModelError, NoSessionError
from pydent.marshaller import SchemaModel, ModelRegistry, fields
from inflection import tableize
import itertools
from copy import deepcopy
from pydent.sessionabc import SessionABC


class ModelBase(SchemaModel):
    """
    Base class for Aquarium models.
    Subclass of :class:`pydent.marshaller.MarshallerBase`

    - creates instances from JSON using `load`
    - contains a reference to the :class:`pydent.session.aqsession.AqSession`
      instance that loaded this model
    """

    PRIMARY_KEY = "id"
    GLOBAL_KEY = "rid"
    SERVER_MODEL_NAME = None
    DEFAULT_COPY_KEEP_UNANONYMOUS = ["Item", "Sample", "Collection"]
    counter = itertools.count()
    id = None
    rid = None

    def __new__(cls, *args, session=None, **kwargs):
        instance = super(ModelBase, cls).__new__(cls)
        instance._session = None
        instance.session = session
        instance._rid = next(ModelBase.counter)
        return instance

    def __init__(self, **data):
        super().__init__(data)
        self.add_data({"rid": self._rid, "id": data.get("id", None)})

    @classmethod
    def _set_data(cls, data, owner):
        if not hasattr(owner, "session"):
            raise NoSessionError(
                "Cannot instantiate new model because its data parent"
                " {} has no 'session' attribute".format(owner)
            )
        instance = cls.__new__(cls, session=owner.session)
        instance.raw = data
        cls.__init__(instance)
        ModelBase.__init__(instance, **data)
        return instance

    @classmethod
    def get_server_model_name(cls):
        if cls.SERVER_MODEL_NAME is None:
            return cls.__name__
        return cls.SERVER_MODEL_NAME

    @classmethod
    def get_tableized_name(cls):
        return tableize(cls.get_server_model_name())

    @property
    def rid(self):
        return self._rid

    @rid.setter
    def rid(self, _rid):
        self._rid = _rid
        self.add_data({"rid": self._rid})

    @property
    def _primary_key(self):
        """Returns the primary key (e.g. 'id') or the rid if id does not exist or is None"""
        if hasattr(self, ModelBase.PRIMARY_KEY):
            pk = getattr(self, ModelBase.PRIMARY_KEY)
            if pk:
                return pk
        return "r{}".format(self.rid)

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
                raise AquariumModelError(
                    "Cannot 'append_to_many.' Model must be a '{}' but found a '{}'".format(
                        field.model, model.__class__.__name__
                    )
                )
            if field.many:
                val = getattr(self, name)
                if val is None:
                    val = []
                    setattr(self, name, val)

                if model.rid not in [m.rid for m in getattr(self, name)]:
                    getattr(self, name).append(model)
        return self

    @classmethod
    def load(cls, *args, **kwargs):
        raise Exception(
            "This method is now depreciated as of version 0.1.0. Trident now requires"
            " model instantiations to be explicitly attached to an AqSession object."
            "\nPlease use the following"
            " methods to initialize your models, which will automatically attach your session object to"
            " the newly constructed instance."
            "\n(1) `session.{name}.new(*args, **kwargs)` to initialize a new model using a constructor."
            "\n(2) `session.{name}.load(data)  # to initialize a model with data."
            "\n(3) `{name}.load_from(data, session)".format(name=cls.__name__)
        )

    @classmethod
    def load_from(cls, data, owner=None):
        """Create a new model instance from loaded attributes.

        'obj' should have a o"""
        if isinstance(data, list):
            models = []
            for d in data:
                model = cls._set_data(d, owner)
                models.append(model)
            return models
        else:
            model = cls._set_data(data, owner)
        return model

    # TODO: rename reload to something else, implement 'refresh' method and associated tests
    def reload(self, data):
        """
        Reload model attributes from new data

        :param data: data to update model instance
        :type data: dict
        :return: model instance
        :rtype: ModelBase
        """
        data_copy = deepcopy(data)
        temp_model = self.__class__.load_from(data_copy, self.session)
        vars(self).update(vars(temp_model))

        return self

    def refresh(self):
        """
        Refresh this model from data from the server.

        :return: self
        :rtype: self
        """
        interface = self.create_interface()
        interface._do_load = False
        data = interface.find(self.id)
        self.reload(data)
        return self

    @classmethod
    def get_relationships(cls):
        grouped = cls._model_schema.grouped_fields
        relationships = grouped[fields.Relationship.__name__]
        alias = grouped[fields.Alias.__name__]
        for aname, alias_field in alias.items():
            aliased = relationships.get(alias_field.alias, None)
            if aliased:
                relationships[aname] = aliased
        return relationships

    @property
    def session(self):
        """The connected session instance."""
        return self._session

    @session.setter
    def session(self, new_session):
        if new_session is not None and not issubclass(type(new_session), SessionABC):
            raise NoSessionError(
                "Cannot instantiate new model because its data parent "
                "session is a type '{}', not a Session object".format(type(new_session))
            )
        if self.session is not None:
            raise Exception(
                "Cannot set session. Model {} already has a session.".format(self)
            )
        self._session = new_session

    def connect_to_session(self, session):
        """Connect model instance to a session. Does nothing if session already exists."""
        self.session = session

    def _check_for_session(self):
        """
        Raises error if model is not connected to a session
        """
        if self.session is None:
            raise NoSessionError(
                "No AqSession instance found for '{name}' but one is required for the method."
                "\nDo one of the following:"
                "\n(1) - Use 'connect_to_session' after initializing your model."
                "\n(2) - If initializing a model use the session model constructor."
                "\n\t >> USE: \t\t'session.{name}.new(*args, **kwargs)'"
                "\n\t >> DO NOT USE:\t'{name}(*args, **kwargs)'"
                "\n(3) - If initializing with load"
                "\n\t >> USE: \t\t'session.{name}.load(data)"
                "\n\t >> DO NOT USE\t'{name}.load(data)".format(
                    name=self.__class__.__name__
                )
            )

    def no_getter(self, *_):
        """Callback that always returns None"""
        return None

    def create_interface(self):
        return self.interface(self.session)

    @classmethod
    def interface(cls, session):
        """Creates a model interface from this class and a session

        This method can be overridden in model definitions for special cases.
        """
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
        return interface.one(query)

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
                clsname=self.__class__.__name__, rid=self.rid, model=model_name
            )
        )
        return model.find(self.session, model_id)

    def where_callback(self, model_name, *args, **kwargs):
        """
        Finds models using a model interface and a set of parameters.

        Used to find models in model relationships.
        """
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
        self.session._log_to_aqhttp(
            "CALLBACK '{clsname}(rid={rid})' made a WHERE request for '{model}'".format(
                clsname=self.__class__.__name__, rid=self.rid, model=model_name
            )
        )
        return model.where(self.session, query_arg, *args[1:], **kwargs)

    def print(self):
        data = self.dump()
        relationships = self.get_relationships()
        data.update(relationships)
        print(data)

    def __str__(self):
        return self._to_str("id", "rid")

    def _to_str(self, *attributes, **kwargs):
        if "rid" not in attributes:
            attributes = list(attributes)
            attributes.append("rid")
        data = self._get_data()
        data.update(kwargs)
        attributes = list(attributes) + list(kwargs)
        return "<{} {}>".format(
            self.__class__.__name__,
            " ".join(["{}={}".format(k, data.get(k, None)) for k in attributes]),
        )

    # TODO: anonymize the keys for relationships as well
    def anonymize(self):
        """
        Resets the primary key of the model and assigns a new rid.

        Metatypes cannot be annonymized.

        :return: self
        """
        if not self.__class__.__name__.endswith("Type"):
            setattr(self, self.PRIMARY_KEY, None)
            setattr(self, "rid", next(self.counter))
            self.updated_at = None
            self.created_at = None
            self.raw = {}
        return self

    def _anonymize_field_keys(self, keep=None):
        for name, relation in self.get_relationships().items():
            if hasattr(relation, "ref"):
                if relation.nested.endswith("Type"):
                    continue
                elif keep and relation.nested in keep:
                    continue
                else:
                    setattr(self, relation.ref, None)

    def copy(self, keep=None):
        """
        Provides a deepcopy of the model, but annonymizes the primary and global keys unless
        class is a metatype (e.g. OperationType, SampleType, FieldType) or class name is
        found in list of 'keep'

        By default, inventory classes such as Sample, Item, and Collection are 'kept'.

        This specific usecase is that when copying whole plans, that the integrity of the
        inventory used in the operations is maintained. These are the items that refer
        to physical inventory in the laboratory and are referred to by their `rids`, and
        so it is important to that any of these inventory are always maintain their `rids`.
        Meaning in the lab, their is only ONE instance of the inventory. In Trident and Aquarium,
        there is only ONE instance of inventory that is referred to by its rid.

        Similarly, any metatype model must also maintain their `rid`.

        :param keep: list of model classes (as a list of strings) to keep un-anonymous
        :return: copied model
        """
        memo = {}
        copied = deepcopy(self, memo)
        if keep is None:
            keep = self.DEFAULT_COPY_KEEP_UNANONYMOUS

        for m in memo.values():
            if issubclass(type(m), ModelBase):
                if keep is None or m.__class__.__name__ not in keep:
                    m.anonymize()
                m._anonymize_field_keys(keep=keep)
        return copied

    @classmethod
    def _flatten_deserialized_data(cls, models, memo):
        """Flattens all of the relationships found in the models, returning a rid: model dictionary"""
        if models is None:
            return memo
        for model in models:

            if model is None or model.rid in memo:
                continue
            else:
                memo[model.rid] = model
                data = model._get_deserialized_data()
                for key in model.get_relationships():
                    val = data.get(key, None)
                    if val is None:
                        continue
                    elif isinstance(val, list):
                        cls._flatten_deserialized_data(val, memo)
                    else:
                        cls._flatten_deserialized_data([val], memo)
        return memo

    def _rid_dict(self):
        """Dictionary of all models attached to this model keyed by their rid"""
        memo = {}
        self._flatten_deserialized_data([self], memo)
        return memo

    def __copy__(self):
        return self.copy()

    #     return cp
    # def patch(self, json_data):
    #     """
    #     Make a patch request to self using json_data.
    #     Reload model instance with new data.
    #     """
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
