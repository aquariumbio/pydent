"""base.py

This module contains the base classes for Trident models. Trident models intelligently load
from JSON and dump to JSON. This is accomplished by adding the '@add_schema' decorator to
classes inherited by the Base class. '@add_schema' dynamically creates a model schema that
handles dumping and loading.

Features of Trident models:

    load - models can be intelligently loaded from JSON data. Hierarchical JSON is loaded intelligently.
        e.g.
            Sample.load(
                {"name": "MyPrimer",
                "sample_type":
                    {"name": "Primer", ...}
                }
            )
            # => <Sample(name="MyPrimer", sample_type=<SampleType(name="Primer")>)>

    dump - models can be dumped to JSON. Dependent models and relationships can be dumped as well.

            s.dump(include=("sample_type"))

    relationships - models relationships are stored
            s = Sample.load(
                {"name": "MyPrimer",
                "sample_type_id": 1}
            )
            primer_type = s.sample_type
            # uses sample_type_id to find the appropriate sample_type model from the database
"""

from pydent.marshaller import MarshallerBase


class ModelBase(MarshallerBase):
    """Base class for Aquarium models. Can create an instance from JSON using "load."
    May contain reference to the session object that created it."""

    def __init__(self, data=None):
        if data is None:
            data = {}
        vars(self).update(data)
        self._session = None

    @property
    def session(self):
        """The connected session object."""
        return self._session

    def connect_to_session(self, session):
        """Connect model instance to a session."""
        if self._session is None:
            self._session = session

    def find(self, model_name, model_id):
        """Finds a model using the model interface and model_id"""
        return self.session.model_interface(model_name).find(model_id)

    def where(self, model_name, params):
        """Finds models using a model interface and a set of parameters."""
        return self.session.model_interface(model_name).where(params)