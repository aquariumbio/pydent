"""
Session class for interacting with Trident and Aquarium

This module defines the AqSession class, which is the main entry point for
accessing the request methods.
Multiple session instances can be created using a user's Aquarium login
information.
From there, the session instance is used to make http requests
(like finding models, updating plans, etc.)

AqSession creates SessionInterfaces which can make http requests to Aquarium
but does not itself make the requests.

Interfaces are accessed by:

(1) session.<ModelName> - access the model interface
(2) session.create - access the create interface
(3) session.update - access the update interface
"""

from pydent.aqhttp import AqHTTP
from pydent.base import ModelRegistry
from pydent.interfaces import ModelInterface, UtilityInterface
from pydent.models import __all__ as allmodels


class AqSession(object):
    """
    Holds an AqHTTP with login information.
    Creates SessionInterfaces for models.

    .. code-block:: python

    session1 = AqSession(username, password, aquairum_url)
    session1.User.find(1)
    # <User(id=1,...)>

    """

    def __init__(self, login, password, aquarium_url, name=None):
        """

        :param login: the Aquarium login for the user
        :type login: str
        :param password: the password for the Aquarium login. This will not be
            stored anywhere. However, login headers for Aquarium will be stored
            in .__aqhttp. This may change in the future with changes
            authentication for the Aquarium API
        :type password: str
        :param aquarium_url: the http formatted Aquarium url
        :type aquarium_url: str
        :param name: (optional) name for this session
        :type name: str or None
        """
        self.name = name
        self.__aqhttp = AqHTTP(login, password, aquarium_url)
        self.__current_user = None

        # initialize model interfaces
        for model_name in allmodels:
            self._register_interface(model_name)

    def _register_interface(self, model_name):
        # get model class f(e.g. "Sample")
        model = ModelRegistry.get_model(model_name)

        # get model interface from model class
        model_interface = model.interface(self)

        # set interface to session attribute (e.g. session.Sample calls Sample model interface)
        setattr(self, model_name, model_interface)

    def set_timeout(self, timeout_in_seconds):
        """Sets the request timeout."""
        self.__aqhttp.timeout = timeout_in_seconds

    @property
    def url(self):
        """Returns the aquarium_url for this session"""
        return self.__aqhttp.aquarium_url

    @property
    def login(self):
        """
        Logs into aquarium, generating the necessary headers to perform requests
        to Aquarium
        """
        return self.__aqhttp.login

    @property
    def current_user(self):
        """
        Returns the current User associated with this session. Returns None
        if no user is found (as in cases where the Aquarium connection is down).
        """
        if self.__current_user is None:
            user = self.User.where({"login": self.__aqhttp.login})
            if not user:
                return None
            self.__current_user = self.User.where(
                {"login": self.__aqhttp.login})[0]
        return self.__current_user

    def logged_in(self):
        """
        Returns whether the user is logged in. If the session
        is able to return the User model instance using the
        session's login credentials, the user is considered
        to be logged in.

        :return: whether user is currently logged in
        :rtype: boolean
        """
        if self.current_user is None:
            return False
        return True

    @property
    def models(self):
        """Returns list of all models available"""
        return list(ModelRegistry.models.keys())

    def model_interface(self, model_name):
        """Returns model interface by name"""
        return ModelInterface(model_name, self.__aqhttp, self)

    @property
    def utils(self):
        """Instantiates a utility interface"""
        return UtilityInterface(self.__aqhttp, self)

    def __repr__(self):
        return "<{}(name={}, AqHTTP={}))>".format(self.__class__.__name__,
                                                  self.name, self.__aqhttp)
