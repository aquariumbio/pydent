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

import inspect
import timeit
import webbrowser
from decimal import Decimal

from requests.exceptions import ReadTimeout

from pydent.aqhttp import AqHTTP
from pydent.base import ModelRegistry
from pydent.interfaces import (
    QueryInterfaceABC,
    QueryInterface,
    UtilityInterface,
    BrowserInterface,
)
from pydent.models import __all__ as allmodels
from pydent.browser import Browser
from pydent.sessionabc import SessionABC
from copy import copy


class AqSession(SessionABC):
    """
    Holds an AqHTTP with login information.
    Creates SessionInterfaces for models.

    .. code-block:: python

    session1 = AqSession(username, password, aquairum_url)
    session1.User.find(1)
    # <User(id=1,...)>

    """

    def __init__(self, login, password, aquarium_url, name=None, aqhttp=None):
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
        self._aqhttp = None
        if login is None and password is None and aquarium_url is None:
            if aqhttp is not None:
                self._aqhttp = aqhttp
            else:
                raise ValueError(
                    "Need either a name, password, and url OR an aqhttp instance."
                )
        else:
            self._aqhttp = AqHTTP(login, password, aquarium_url)
        self._current_user = None
        self._interface_class = QueryInterface
        self.initialize_interfaces()
        self._browser = None
        self._using_cache = False
        self.init_cache()

    @property
    def interface_class(self):
        return self._interface_class

    @interface_class.setter
    def interface_class(self, c):
        if not issubclass(c, QueryInterfaceABC):
            raise ValueError(
                "Interface {} is not a subclass of {}".format(
                    type(c), QueryInterfaceABC
                )
            )
        self._interface_class = c

    def initialize_interfaces(self):
        # initialize model interfaces
        for model_name in allmodels:
            self._register_interface(model_name)

    def open(self):
        webbrowser.open(self._aqhttp.url)

    @property
    def session(self):
        return self

    def set_verbose(self, verbose, tb_limit=None):
        self._aqhttp.log.set_verbose(verbose, tb_limit=tb_limit)

    def _log_to_aqhttp(self, msg):
        """Sends a log message to the aqhttp's logger"""
        self._aqhttp.log.info(msg)

    def _register_interface(self, model_name):
        # get model interface from model class
        model_interface = self.interface_class(model_name, self._aqhttp, self)

        # set interface to session attribute (e.g. session.Sample calls Sample model interface)
        setattr(self, model_name, model_interface)

    def set_timeout(self, timeout_in_seconds):
        """Sets the request timeout."""
        self._aqhttp.timeout = timeout_in_seconds

    @property
    def url(self):
        """Returns the aquarium_url for this session"""
        return self._aqhttp.aquarium_url

    @property
    def login(self):
        """
        Logs into aquarium, generating the necessary headers to perform requests
        to Aquarium
        """
        return self._aqhttp.login

    @property
    def current_user(self):
        """
        Returns the current User associated with this session. Returns None
        if no user is found (as in cases where the Aquarium connection is down).
        """
        if self._current_user is None:
            user = self.User.where({"login": self._aqhttp.login})
            if not user:
                return None
            self._current_user = self.User.where({"login": self._aqhttp.login})[0]
        return self._current_user

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

    def model_interface(self, model_name, interface_class=None):
        """Returns model interface by name"""
        if interface_class is None:
            interface_class = self.interface_class
        return interface_class(model_name, self._aqhttp, self)

    @property
    def utils(self):
        """Instantiates a utility interface"""
        return UtilityInterface(self._aqhttp, self)

    # TODO: put 'ping' in documentation
    def ping(self, num=5):
        """Performs a number of simple requests (pings) to estimate the speed of the server.
        Displays a message about the average time each ping took."""
        try:
            ping_function = lambda: self.User.find(1)
            ping_function_source = inspect.getsource(ping_function).strip()
            secs = timeit.timeit(ping_function, number=num)
            print(
                "{} pings (using the function '{}')".format(num, ping_function_source)
            )
            print("{} seconds per ping".format("%.2E" % Decimal(secs / num)))
            return secs
        except ReadTimeout as e:
            print("Error: {}".format(e))
            print(
                "Aquarium ({}) looks like its down. The function '{}' raised a {} exception, but should not have.".format(
                    self.url, ping_function_source, ReadTimeout
                )
            )
            return None

    @property
    def browser(self):
        return self._browser

    def init_cache(self):
        self._browser = Browser(self)

    def clear_cache(self):
        self.browser.clear()

    @property
    def using_requests(self):
        return self._aqhttp._using_requests

    @using_requests.setter
    def using_requests(self, b):
        if b:
            self._aqhttp.on()
        else:
            self._aqhttp.off()

    @property
    def using_cache(self):
        return self._using_cache

    @using_cache.setter
    def using_cache(self, b):
        if b:
            self.interface_class = BrowserInterface
            if self.browser is None:
                self.init_cache()
            self.initialize_interfaces()
            self._using_cache = True
        else:
            self._using_cache = False
            self.interface_class = QueryInterface
            self.initialize_interfaces()

    def copy(self):
        instance = self.__class__(
            None, None, None, self.name, aqhttp=copy(self._aqhttp)
        )
        instance.using_requests = self.using_requests
        instance.using_cache = self.using_cache
        return instance

    def with_cache(
        self, using_requests=None, using_models=False, timeout=None, verbose=None
    ):
        return self(
            using_cache=True,
            using_models=using_models,
            using_requests=using_requests,
            timeout=timeout,
            using_verbose=verbose,
        )

    def with_requests_off(
        self, using_cache=None, using_models=True, timeout=None, verbose=None
    ):
        return self(
            using_cache=using_cache,
            using_models=using_models,
            using_requests=False,
            timeout=timeout,
            using_verbose=verbose,
        )

    @staticmethod
    def _swap_sessions(from_session, to_session):
        """Moves models from one sesssion to another."""
        models = from_session.browser.models
        if to_session.browser:
            to_session.browser.update_cache(models)
        for m in models:
            m._session = to_session

    def __call__(
        self,
        using_cache=None,
        using_requests=None,
        timeout=None,
        using_models=None,
        using_verbose=None,
    ):
        new_session = self.copy()
        new_session.parent_session = self
        if using_cache is not None:
            new_session.using_cache = using_cache
        if using_requests is not None:
            new_session.using_requests = using_requests
        if timeout is not None:
            new_session.set_timeout(timeout)
        if using_models and self.browser:
            new_session.browser.update_cache(self.browser.models)
        if using_verbose is not None:
            new_session.set_verbose(using_verbose)
        return new_session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "parent_session"):
            self._swap_sessions(self, self.parent_session)

    def __repr__(self):
        return "<{}(name={}, AqHTTP={}))>".format(
            self.__class__.__name__, self.name, self._aqhttp
        )
