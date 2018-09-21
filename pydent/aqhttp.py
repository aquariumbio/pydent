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

import requests

from pydent.exceptions import (TridentRequestError, TridentLoginError,
                               TridentTimeoutError, TridentJSONDataIncomplete)
from pydent.utils import url_build


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

    @property
    def url(self):
        """An alias of aquarium_url"""
        return self.aquarium_url

    @staticmethod
    def create_session_json(login, password):
        return {"session": {
            "login": login,
            "password": password
        }}

    def _login(self, login, password):
        """
        Login to aquarium and saves header as a requests.Session()
        """
        session_data = self.create_session_json(login, password)
        try:
            res = requests.post(url_build(self.aquarium_url, "sessions.json"),
                                json=session_data, timeout=self.timeout)

            cookies = dict(res.cookies)

            # Check for remember token
            if not any(["remember_token" in k for k in dict(res.cookies)]):
                raise TridentLoginError(
                    "Authentication error. Remember token not found in login request."
                    " Contact developers."
                )

            # fix remember token (for some outdated versions of Aquarium)
            for c in dict(cookies):
                if "remember_token" in c:
                    cookies["remember_token"] = cookies[c]
            # TODO: do we remove the session cookie to handle asynchronous requests?
            self.cookies = dict(cookies)
        except requests.exceptions.MissingSchema as error:
            raise TridentLoginError(
                "Aquarium URL {0} incorrectly formatted. {1}".format(
                    self.aquarium_url, error.args[0]))
        except requests.exceptions.ConnectTimeout:
            raise TridentTimeoutError(
                "Either Aquarium took too long to respond during login or your internet"
                " connection is slow. Make sure the url {} is correct."
                " Alternatively, use Session.set_timeout"
                " to increase the request timeout.".format(self.aquarium_url))

    @staticmethod
    def _serialize_request(url, method, body):
        return json.dumps({
            "url": url,
            "method": method,
            "body": body
        }, sort_keys=True)

    def request(self, method, path, timeout=None, allow_none=True, **kwargs):
        """
        Performs a http request.

        :param method: request method (e.g. 'put', 'post', 'get', etc.)
        :type method: str
        :param path: url to perform the request
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
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

        key = self._serialize_request(url, method, body)
        result = None

        if result is None:
            result = requests.request(
                method,
                url_build(
                    self.aquarium_url, path),
                timeout=timeout,
                cookies=self.cookies,
                **kwargs)

        return self._response_to_json(result)

    def _response_to_json(self, result):
        """
        Turns :class:`requests.Request` instance into a json.
        Raises TridentRequestError if an error occurs.
        """

        if result.url == url_build(self.aquarium_url, "signin"):
            msg = "There was an error with authenticating the request. Aquarium " + \
            "re-routed to the sign-in page."
            raise TridentRequestError(msg, result)

        try:
            result_json = result.json()
        except json.JSONDecodeError:
            msg = "Response is not JSON formatted"
            msg += "\nMessage:\n" + result.text
            raise TridentRequestError(msg, result)
        if result_json and 'errors' in result_json:
            errors = result_json['errors']
            if isinstance(errors, list):
                errors = "\n".join(errors)
            msg = "Error response:\n{}".format(errors)
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

    def post(self, path, json_data=None, timeout=None, allow_none=True, **kwargs):
        """
        Make a post request to the session

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error if json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("post", path, json=json_data, timeout=timeout,
                            allow_none=allow_none, **kwargs)

    def put(self, path, json_data=None, timeout=None, allow_none=True, **kwargs):
        """
        Make a put request to the session

        :param path: url
        :type path: str
        :param json_data: json_data to post
        :type json_data: dict
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error when json_data contains a null
                or None value (default True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("put", path, json=json_data, timeout=timeout,
                            allow_none=allow_none, **kwargs)

    def get(self, path, timeout=None, allow_none=True, **kwargs):
        """
        Make a get request to the session

        :param path: url
        :type path: str
        :param timeout: time in seconds to process request before raising
                exception
        :type timeout: int
        :param allow_none: if False throw error when json_data contains a null
                or None value (default: True)
        :type allow_none: boolean
        :param kwargs: additional arguments to post to request
        :type kwargs: dict
        :return: json
        :rtype: dict
        """
        return self.request("get", path, timeout=timeout,
                            allow_none=allow_none, **kwargs)

    def delete(self, path, timeout=None, **kwargs):
        return self.request("delete", path, timeout=timeout, **kwargs)

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__,
                                     self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()
