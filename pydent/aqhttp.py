"""
Request class for making raw http requests to Aquarium

This module contains the AqHTTP class, which can make arbitrary post/put/get
requests to Aquarium and returns JSON data.

Generally, Trident users should be unable to make arbitrary requests using this
class.
Users should only access these methods indirectly through a ``Session`` or
``SessionInterface`` instance.
"""

import json
import re

import requests

from pydent.exceptions import (TridentRequestError, TridentLoginError,
                               TridentTimeoutError, TridentJSONDataIncomplete)
from pydent.utils import url_build


# TODO: Replace request history with save_attr in models?
class AqHTTP(object):
    """
    Defines a session/connection to Aquarium.
    Makes HTTP requests to Aquarium and returns JSON.

    This class should be obscured from Trident user so that users cannot make
    arbitrary requests to an Aquarium server and get sensitive information
    (e.g. User json that is returned contains api_key, password_digest, etc.)
    or make damaging posts.
    Instead, a SessionInterface should be the object that makes these requests.
    """

    TIMEOUT = 10

    def __init__(self, login, password, aquarium_url):
        """
        Initializes an aquarium session with login, password, and server.

        :param login: Aquarium login
        :type login: str
        :param aquarium_url: aquarium url to the server
        :type aquarium_url: str
        """
        self.login = login
        self.aquarium_url = aquarium_url
        self._requests_session = None
        self.timeout = self.__class__.TIMEOUT
        self._login(login, password)
        self.request_history = {}

    @staticmethod
    def create_session_json(login, password):
        """Formats login information for aquarium"""
        return {
            "session": {
                "login": login,
                "password": password
            }
        }

    @property
    def url(self):
        """An alias of aquarium_url"""
        return self.aquarium_url

    def _login(self, login, password):
        """
        Login to aquarium and saves header as a requests.Session()
        """
        session_data = self.__class__.create_session_json(login, password)
        res = None
        try:
            res = requests.post(url_build(self.aquarium_url, "sessions.json"),
                                json=session_data, timeout=self.timeout)
        except requests.exceptions.MissingSchema as error:
            raise TridentLoginError(
                "Aquairum URL {0} incorrectly formatted. {1}".format(
                    self.aquarium_url, error.args[0]))
        except requests.exceptions.ConnectTimeout:
            raise TridentTimeoutError(
                "Aquarium took too long to respond during login. Make sure "
                "the url {} is correct. Alternatively, use Session.set_timeout"
                " to increase the request timeout.".format(self.aquarium_url))
        headers = res.headers
        if 'set-cookie' not in headers:
            raise TridentLoginError(
                "Could not find proper login header for Aquarium.")
        headers = {"cookie": self.__class__.fix_remember_token(
            res.headers["set-cookie"])}
        self._requests_session = requests.Session()
        self._requests_session.headers.update(headers)

    @staticmethod
    def fix_remember_token(header):
        """ Fixes the Aquarium specific remember token """
        parts = header.split(';')
        rtok = ""
        for part in parts:
            cparts = part.split('=')
            if re.match('remember_token', cparts[0]):
                rtok = cparts[1]
        return "remember_token=" + rtok + "; " + header

    def clear_history(self):
        """Clears the request history."""
        self.request_history = {}

    @staticmethod
    def _serialize_request(url, method, body):
        return json.dumps({
            "url": url,
            "method": method,
            "body": body
        }, sort_keys=True)

    def request(self, method, path, timeout=None,
                get_from_history_ok=False, allow_none=True, **kwargs):
        """
        Performs a http request.

        :param method: request method (e.g. 'put', 'post', 'get', etc.)
        :type method: str
        :param path: url to perform the request
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param get_from_history_ok: whether its ok to return previously found
                request from history (default=False)
        :type get_from_history_ok: boolean
        :param allow_none: if False will raise error when json_data
                contains a None or null value (default: True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        if timeout is None:
            timeout = self.timeout
        if not allow_none and 'json' in kwargs:
            self._disallow_null_in_json(kwargs['json'])

        # serialize request
        url = url_build(self.aquarium_url, path)
        body = {}
        if 'json' in kwargs:
            body = kwargs['json']

        # get result from history (if ok) otherwise, make a http request;
        # save result to history
        key = self._serialize_request(url, method, body)
        result = None
        if get_from_history_ok:
            result = self.request_history.get(key, None)
        if result is None:
            result = self._requests_session.request(
                method,
                url_build(
                    self.aquarium_url, path),
                timeout=timeout,
                **kwargs)
            self.request_history[key] = result
        return self._response_to_json(result)

    @staticmethod
    def _response_to_json(result):
        """
        Turns :class:`requests.Request` instance into a json.
        Raises TridentRequestError if an error occurs.
        """
        try:
            result_json = result.json()
        except json.JSONDecodeError:
            msg = "Response is not JSON formatted"
            msg += "\nMessage:\n" + result.text
            raise TridentRequestError(msg, result)
        if result_json and 'errors' in result_json:
            errors = result_json['errors']
            msg = "Error response:\n{}".format("\n".join(errors))
            raise TridentRequestError(msg, result)
        return result_json

    @staticmethod
    def _disallow_null_in_json(json_data):
        """
        Raises :class:pydent.exceptions.TridentJSONDataIncomplete exception if
        json data being sent contains a null value
        """
        if None in json_data.values():
            raise TridentJSONDataIncomplete(
                "JSON data {} contains a null value.".format(json_data))

    def post(self, path, json_data=None, timeout=None,
             get_from_history_ok=False, allow_none=True, **kwargs):
        """
        Make a post request to the session

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param get_from_history_ok: whether its ok to return previously found
                request from history (default=False)
        :type get_from_history_ok: boolean
        :param allow_none: if False throw error if json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("post", path, json=json_data, timeout=timeout,
                            get_from_history_ok=get_from_history_ok,
                            allow_none=allow_none, **kwargs)

    def put(self, path, json_data=None, timeout=None,
            get_from_history_ok=False, allow_none=True, **kwargs):
        """
        Make a put request to the session

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param get_from_history_ok: whether its ok to return previously found
                request from history (default=False)
        :type get_from_history_ok: boolean
        :param allow_none: if False throw error when json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("put", path, json=json_data, timeout=timeout,
                            get_from_history_ok=get_from_history_ok,
                            allow_none=allow_none, **kwargs)

    def get(self, path, timeout=None,
            get_from_history_ok=False, allow_none=True, **kwargs):
        """
        Make a get request to the session

        :param path: url
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param get_from_history_ok: whether its ok to return previously found
                request from history (default=False)
        :type get_from_history_ok: boolean
        :param allow_none: if False throw error when json_data contains a null
                or None value (default: True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("get", path, timeout=timeout,
                            get_from_history_ok=get_from_history_ok,
                            allow_none=allow_none, **kwargs)

    def delete(self, path, timeout=None, **kwargs):
        return self.request("delete", path, timeout=timeout, **kwargs)

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__,
                                     self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()
