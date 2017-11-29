"""Base Aquarium model

This module contains the base classes for Trident models. Trident models intelligently load
from JSON and dump to JSON. This is accomplished by adding the '@add_schema' decorator to
classes inherited by the Base class. '@add_schema' dynamically creates a model schema that
handles dumping and loading.

Features of Trident models:

    load - models can be intelligently loaded from JSON data. Hierarchical JSON is loaded
    intelligently.

.. code-block:: python

    Sample.load({"name": "MyPrimer", "sample_type": {"name": "Primer", ...} })
    # => <Sample(name="MyPrimer", sample_type=<SampleType(name="Primer")>)>

dump - models can be dumped to JSON. Dependent models and relationships can be dumped as well.

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

from functools import wraps

from pydent.exceptions import TridentModelNotFoundError
from pydent.marshaller import MarshallerBase
from pydent.utils import pprint

class ModelRegistry(type):
    """Stores a list of models that can be accessed by name."""
    models = {}

    def __init__(cls, name, bases, selfdict):
        """Class initializer. Called when a class is 'subclassed.' Saves model to the registry"""
        super().__init__(name, bases, selfdict)
        if not name == "ModelBase":
            ModelRegistry.models[name] = cls

    @staticmethod
    def get_model(model_name):
        """Gets model by model_name"""
        if model_name not in ModelRegistry.models:
            raise TridentModelNotFoundError("Model \"{}\" not found in ModelRegistry.".format(model_name))
        else:
            return ModelRegistry.models[model_name]

    def __getattr__(self, item):
        """Special warning for attribute errors. Its likely that user may have wanted to use
        a model interface instead of the Base class."""
        raise AttributeError("'{0}' has no attribute '{1}'. Method may be a ModelInterface method."
                             " Did you mean '<yoursession>.{0}.{1}'?"
                             .format(self.__name__, item))


def custom_type_error(fxn):
    @wraps(fxn)
    def wrapped(*args, **kwargs):
        return fxn(*args, **kwargs)

    return wrapped


class ModelBase(MarshallerBase, metaclass=ModelRegistry):
    """Base class for Aquarium models. Subclass of :class:`pydent.marshaller.MarshallerBase`

    - creates instances from JSON using `load`
    - contains a reference to the :class:`pydent.session.aqsession.AqSession` instance that loaded this model
    """

    def __init__(self):
        self._session = None

    @property
    def session(self):
        """The connected session instance."""
        return self._session

    def connect_to_session(self, session):
        """Connect model instance to a session. Does nothing if session already exists."""
        if self._session is None:
            self._session = session

    def _check_for_session(self):
        if self.session is None:
            raise AttributeError("No AqSession instance found for '{}'. Use 'connect_to_session' "
                                 "to connect this model to a session".format(self.__class__.__name__))

    def find_using_session(self, model_name, model_id):
        """Finds a model using the model interface and model_id. Used to find
        models in model relationships."""
        self._check_for_session()
        return self.session.model_interface(model_name).find(model_id)

    def where_using_session(self, model_name, params):
        """Finds models using a model interface and a set of parameters. Used to
        find models in model relationships."""
        self._check_for_session()
        return self.session.model_interface(model_name).where(params)

    def print(self, *args, **kwargs):
        """
        Prints the model instance in a nice format. See :func:`pydent.marshaller.marshallerbase.dump`

        :param args: dump arguments
        :param kwargs: dump arguments
        :return:
        """
        pprint(self.dump(*args, **kwargs))

