"""
Session (:mod:`pydent.aqsession`)
=================================

.. currentmodule:: pydent.aqsession

Session class for interacting with Trident and Aquarium. To initialize
a new session, you'll need your Aquarium login credentials and an Aquarium url:

.. code-block:: python

    from pydent import AqSession
    session = AqSession('joeshmoe', 'pass123', 'http://myaquariumurl.org`)

.. note::
    To login discretely with a hidden password, you may use
    the :meth:`pydent.login <pydent.login>` method.

After initializing a session, models are accessible from the Session:

.. code-block:: python

    sample = session.Sample.one()
    last50 = session.Item.last(50)
    first10 = session.SampleType.first(10)
    mysamples = session.Sample.last(10, query={'user_id': 66})

.. see also::
    Models :ref:`Models <models>`
        documentation on manipulating and querying models.
    Temporary Sessions :ref:`Cache <cache>`
        documentation on how to use the session cache to
        speed up queries.


User Objects
------------

The AqSession and Browser are the main interaction objects for querying the
Aquarium server. The Browser class provides special methods for speeding
up and caching results from the server, which is covered in
:ref:`Advanced Topics <cache>`.

.. currentmodule: pydent.aqsession

.. autosummary::
    :toctree: generated/

    AqSession
    Browser

.. currentmodule: pydent.planner.planner

Non-User Objects
----------------

These modules provide utility support for Trident. These are not relevant for most
users.

.. currentmodule: pydent.aqsession

.. autosummary::
    :toctree: generated/

    SessionABC
    AqHTTP

Interfaces
^^^^^^^^^^

.. currentmodule:: pydent.interfaces

Interfaces govern how the session searches, loads, and dumps
Aquarium models from the server.

.. autosummary::
    :toctree: generated/

    BrowserInterface
    CRUDInterface
    QueryInterface
    QueryInterfaceABC
    SessionInterface
    UtilityInterface

"""
import inspect
import timeit
import webbrowser
from copy import copy
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Type
from typing import Union

from requests.exceptions import ReadTimeout

from pydent.aqhttp import AqHTTP
from pydent.aql import aql
from pydent.aql import aql_schema
from pydent.base import ModelBase
from pydent.base import ModelRegistry
from pydent.browser import Browser
from pydent.interfaces import BrowserInterface
from pydent.interfaces import QueryInterface
from pydent.interfaces import QueryInterfaceABC
from pydent.interfaces import SessionInterface
from pydent.interfaces import UtilityInterface
from pydent.inventory_updater import save_inventory
from pydent.models import __all__ as allmodels
from pydent.sessionabc import SessionABC


class AqSession(SessionABC):
    """Holds an AqHTTP with login information. Creates SessionInterfaces for
    models.

    .. code-block:: python

        session1 = AqSession(username, password, aquarium_url)
        session1.User.find(1)
        # <User(id=1,...)>
    """

    def __init__(
        self,
        login: str,
        password: str,
        aquarium_url: str,
        name: str = None,
        aqhttp: str = None,
    ):
        """Initializes a new trident Session.

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
        self._aqhttp = None  #: requests interface
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
        self._initialize_interfaces()
        self._browser = None  #: the sessions browser
        self._using_cache = False
        self.init_cache()
        self.parent_session = (
            None  #: the parent session, if derived from another session
        )

    @property
    def interface_class(self) -> Type:
        """Returns the session's interface class."""
        return self._interface_class

    @interface_class.setter
    def interface_class(self, c: Type):
        """Sets the session's interface class."""
        if not issubclass(c, QueryInterfaceABC):
            raise ValueError(
                "Interface {} is not a subclass of {}".format(
                    type(c), QueryInterfaceABC
                )
            )
        self._interface_class = c

    def _initialize_interfaces(self):
        """Initializes the session's interfaces."""
        # initialize model interfaces
        for model_name in allmodels:
            self._register_interface(model_name)

    def open(self):
        """Open Aquarium in a web browser window."""
        webbrowser.open(self._aqhttp.url)

    @property
    def session(self) -> "AqSession":
        """Return self."""
        return self

    def set_verbose(self, verbose: bool, tb_limit: int = None):
        self._aqhttp.log.set_verbose(verbose, tb_limit=tb_limit)

    def _log_to_aqhttp(self, msg: str):
        """Sends a log message to the aqhttp's logger."""
        self._aqhttp.log.info(msg)

    def _register_interface(self, model_name: str):
        # get model interface from model class
        model_interface = self.interface_class(model_name, self._aqhttp, self)

        # set interface to session attribute (e.g. session.Sample calls Sample model interface)
        setattr(self, model_name, model_interface)

    def set_timeout(self, timeout_in_seconds: int):
        """Sets the request timeout."""
        self._aqhttp.timeout = timeout_in_seconds

    @property
    def url(self):
        """Returns the aquarium_url for this session."""
        return self._aqhttp.aquarium_url

    @property
    def login(self) -> str:
        """Logs into aquarium, generating the necessary headers to perform
        requests to Aquarium."""
        return self._aqhttp.login

    @property
    def current_user(self) -> "ModelBase":
        """Returns the current User associated with this session.

        Returns None if no user is found (as in cases where the Aquarium
        connection is down).
        """
        if self._current_user is None:
            user = self.User.where({"login": self._aqhttp.login})
            if not user:
                return None
            self._current_user = self.User.where({"login": self._aqhttp.login})[0]
        return self._current_user

    def logged_in(self) -> bool:
        """Returns whether the user is logged in. If the session is able to
        return the User model instance using the session's login credentials,
        the user is considered to be logged in.

        :return: whether user is currently logged in
        :rtype: boolean
        """
        if self.current_user is None:
            return False
        return True

    @property
    def models(self) -> List[str]:
        """Returns list of all models available."""
        return list(ModelRegistry.models.keys())

    def model_interface(
        self, model_name: str, interface_class: SessionInterface = None
    ) -> SessionInterface:
        """Returns model interface by name."""
        if interface_class is None:
            interface_class = self.interface_class
        return interface_class(model_name, self._aqhttp, self)

    @property
    def utils(self):
        """Instantiates a utility interface."""
        return UtilityInterface(self._aqhttp, self)

    def _ping_function(self):
        return self.User.one()

    # TODO: put 'ping' in documentation
    def ping(self, num: int = 5) -> Union[None, int]:
        """Performs a number of simple requests (pings) to estimate the speed
        of the server.

        Displays a message about the average time each ping took.
        """
        ping_function = self._ping_function()
        ping_function_source = inspect.getsource(ping_function).strip()
        try:
            secs = timeit.timeit(ping_function, number=num)
            print(
                "{} pings (using the function '{}')".format(num, ping_function_source)
            )
            print("{} seconds per ping".format("%.2E" % Decimal(secs / num)))
            return secs
        except ReadTimeout as e:
            print("Error: {}".format(e))
            print(
                "The Aquarium server ({}) looks like its down. The function '{}' "
                "raised a {} exception, but should not have.".format(
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
    def using_requests(self) -> bool:
        return self._aqhttp._using_requests

    @using_requests.setter
    def using_requests(self, b: bool):
        if b:
            self._aqhttp.on()
        else:
            self._aqhttp.off()

    @property
    def using_cache(self) -> bool:
        return self._using_cache

    @using_cache.setter
    def using_cache(self, b: bool):
        if b:
            self.interface_class = BrowserInterface
            if self.browser is None:
                self.init_cache()
            self._initialize_interfaces()
            self._using_cache = True
        else:
            self._using_cache = False
            self.interface_class = QueryInterface
            self._initialize_interfaces()

    def copy(self):
        instance = self.__class__(
            None, None, None, self.name, aqhttp=copy(self._aqhttp)
        )
        instance.using_requests = self.using_requests
        instance.using_cache = self.using_cache
        return instance

    def with_cache(
        self,
        using_requests: bool = None,
        using_models: bool = False,
        timeout: int = None,
        verbose=None,
    ) -> "AqSession":
        """

        :param using_requests: if False, ForbiddenRequest will be raised if \
            requests are made using the session.
        :param using_models: if True (default: False), derived session will \
            inherit the current sessions model_cache
        :param timeout: the requests timeout in seconds
        :param verbose: if True, verbose mode will be activated for the derived session
        :return:
        """
        return self(
            using_cache=True,
            using_models=using_models,
            using_requests=using_requests,
            timeout=timeout,
            using_verbose=verbose,
        )

    def with_requests_off(
        self,
        using_cache: bool = None,
        using_models: bool = True,
        timeout: int = None,
        verbose=None,
    ) -> "AqSession":
        return self(
            using_cache=using_cache,
            using_models=using_models,
            using_requests=False,
            timeout=timeout,
            using_verbose=verbose,
        )

    @staticmethod
    def _swap_sessions(from_session, to_session):
        """Moves models from one session to another."""
        if to_session:
            models = from_session.browser.models
            if to_session.browser:
                to_session.browser.update_cache(models)
            for m in models:
                m._session = to_session

    @classmethod
    def query_schema(cls) -> Dict:
        return aql_schema

    def query(self, data: Dict, use_cache: bool = False) -> List[ModelBase]:
        """Perform a complex query a complex JSON query object.

        Check out the :ref:`JSON Schema page <json_schema>` for more information.

        You may also checkout `AqSession.query_schema` to view the JSON schema
        that validates the input.

        .. code-block:: python

            {
              "__model__": "Item",
              "__description__": "Get available primers in last 7 days",
              "query": {
                "object_type": {
                  "query": {
                    "sample_type": {
                      "query": {
                        "name": "Primer"
                      }
                    }
                  }
                },
                "created_at": {
                  "__time__": {
                    "__days__": -7
                  }
                },
                "location": {
                    "__not__": "deleted"
                }
                "__options__": {
                  "limit": 1
                }
              }
            }

        ..versionadded:: 0.1.5a16
            Added query method for complex queries

        .. versionchanged:: 0.1.5a23 `query` key now changed to `__query__`

        :param data: data query
        :param use_cache: whether to inherit the cache from the provided session
            (default: False)
        :return: list of models fitting the query
        :raises: AquariumQueryLanguageValidationError if input data is invalid.
        """
        return aql(self, data, use_cache=use_cache)

    def __getattr__(self, item):
        if item not in self.__dict__:
            non_private = [k for k in QueryInterface.__dict__ if not k.startswith("_")]
            if item in non_private:
                raise AttributeError(
                    "{s} has no attribute '{item}'.\nDid you mean "
                    "'session.[ModelName].{item}'?".format(s=self.__class__, item=item)
                )
            else:
                msg = ModelRegistry.did_you_mean_model(item, fallback=False)
                if msg:
                    raise AttributeError(
                        "{s} has no attribute '{item}'.\n{msg}".format(
                            s=self.__class__, item=item, msg=msg
                        )
                    )

        return self.__getattribute__(item)

    def __call__(
        self,
        using_cache: bool = None,
        using_requests: bool = None,
        timeout: int = None,
        using_models: bool = None,
        using_verbose: bool = None,
        session_swap: bool = False,
    ) -> "AqSession":
        """Factory call for producing a new Session instance.

        .. versionchanges:: 0.1.5a7
            'session_swap` parameter added.

        :param using_cache:
        :param using_requests:
        :param timeout:
        :param using_models:
        :param using_verbose:
        :param session_swap:
        :return:
        """
        new_session = self.copy()
        new_session.parent_session = self
        if using_cache is not None:
            new_session.using_cache = using_cache
        if using_requests is not None:
            new_session.using_requests = using_requests
        if timeout is not None:
            new_session.set_timeout(timeout)
        if session_swap:
            self._swap_sessions(self, new_session)
        elif using_models and self.browser:
            new_session.browser.update_cache(self.browser.models)
        if using_verbose is not None:
            new_session.set_verbose(using_verbose)
        return new_session

    def __enter__(self) -> "AqSession":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "parent_session"):
            self._swap_sessions(self, self.parent_session)

    def __repr__(self) -> str:
        return "<{}(name={}, AqHTTP={}), parent={})>".format(
            self.__class__.__name__, self.name, self._aqhttp, id(self.parent_session)
        )
