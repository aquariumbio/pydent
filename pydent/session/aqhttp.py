"""aqhttp.py

This module contains the AqHTTP class, which can make arbitrary post/put/get/etc. requests to
Aquarium and returns JSON data.

Generally, Trident users should be unable to make arbitrary requests using this class. Users should
only be able to access these methods second-hand through a Session/SessionInterface instances.
"""

import json
import os
import re

import requests
import warnings

from pydent.exceptions import TridentRequestError, TridentLoginError, TridentTimeoutError, TridentJSONDataIncomplete


class AqHTTP(object):
    """Defines a session/connection to Aquarium. Makes HTTP requests to Aquarium and returns JSON.

    This class should be generally
    obscured from Trident user so that users cannot make arbitrary requests to an Aquarium server
    and get sensitive information (e.g. User json that is returned contains api_key,
    password_digest, etc.) or make damaging posts. Instead, a SessionInterface should be the object
    that makes these requests.
    """

    TIMEOUT = 10

    def __init__(self, login, password, aquarium_url):
        """
        Initializes an aquarium session with login, password, server combination

        :param login: Aquarium login
        :type login: basestring
        :param aquarium_url: aquarium url to the server
        :type aquarium_url: basestring
        """
        self.login = login
        self.aquarium_url = aquarium_url
        self._requests_session = None
        self.timeout = self.__class__.TIMEOUT
        self._login(login, password)

    @staticmethod
    def create_session_json(login, password):
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

    # TODO: encrypt the header, store key in separate file (not accessible after pip install)
    def _login(self, login, password):
        """ Login to aquarium and saves header as a requests.Session() """
        session_data = self.__class__.create_session_json(login, password)
        res = None
        try:
            res = requests.post(os.path.join(self.aquarium_url, "sessions.json"),
                                json=session_data, timeout=self.timeout)
        except requests.exceptions.MissingSchema as error:
            raise TridentLoginError("Aquairum URL {0} incorrectly formatted. {1}".format(
                self.aquarium_url, error.args[0]))
        except requests.exceptions.ConnectTimeout as error:
            raise TridentTimeoutError("Aquarium took too long to respond during login. Make sure "
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

    # TODO: return warnings about not finding
    def request(self, method, path, timeout=None, **kwargs):
        """Performs a generic request using the the requests session created during login."""
        if timeout is None:
            timeout = self.timeout
        if 'json' in kwargs:
            self._disallow_null_in_json(kwargs['json'])
        result = self._requests_session.request(method, os.path.join(self.aquarium_url, path), timeout=timeout,
                                                    **kwargs)
        return self._request_to_json(result)
        # except TridentJSONDataIncomplete as e:
        #     warnings.warn(str(e.args))
        #     return None
        # except TridentRequestError as e:
        #     warnings.warn(str(e.args))
        #     return None


    def _request_to_json(self, result):
        try:
            result_json = result.json()
        except json.JSONDecodeError:
            raise TridentRequestError(
                "<StatusCode: {code} ({reason})> "
                "Response is not JSON formatted. "
                "Trident may not be properly connected to the server. "
                "Verify login credentials.".format(code=result.status_code, reason=result.reason))
        if "errors" in result_json:
            raise TridentRequestError(
                "Request: {}\n{}\n{}".format(result.request.body, result, result_json['errors'])
            )
        return result_json

    def _disallow_null_in_json(self, json_data):
        """Raises :class:pydent.exceptions.TridentJSONDataIncomplete exception if json data being sent
        contains a null value"""
        if None in json_data.values():
            raise TridentJSONDataIncomplete("JSON data {} contains a null value.".format(json_data))

    def post(self, path, json_data=None, timeout=None, **kwargs):
        """ Makes a post request to the session """
        return self.request("post", path, json=json_data, timeout=timeout, **kwargs)

    def put(self, path, json_data=None, timeout=None, **kwargs):
        """ Makes a put request to the session """
        return self.request("put", path, json=json_data, timeout=timeout, **kwargs)

    def get(self, path, timeout=None, **kwargs):
        """ Makes a get request to the session """
        return self.request("get", path, timeout=timeout, **kwargs)

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__, self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()
