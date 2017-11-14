"""aqhttp.py

This module contains the AqHTTP class, which can make arbitrary post/put/get/etc. requests to Aquarium and
returns JSON data.

Generally, Trident users should be unable to make arbitrary requests using this class. Users should only
be able to access these methods second-hand through a Session/SessionInterface instances.
"""

import json
import os
import re

import requests

from pydent.exceptions import TridentRequestError, TridentLoginError, TridentTimeoutError


def to_json(fxn):
    """ returns formated the request response as a JSON.
    Throws exception if response is not formatted properly."""

    def wrapper(*args, **kwargs):
        result = fxn(*args, **kwargs)
        try:
            result = result.json()
        except json.JSONDecodeError:
            raise TridentRequestError(
                "Response is not JSON formatted. Trident is probably not properly "
                "connected to the server. Verify login credentials.")
        except requests.exceptions.ConnectTimeout:
            raise TridentTimeoutError("Aquarium took too long to respond. Make sure the url "
                                      "{} is correct.".format(args[0].aquarium_url))
        if "errors" in result:
            raise TridentRequestError(
                str(result["errors"])
            )
        return result

    return wrapper


class AqHTTP(object):
    """Defines a session/connection to Aquarium. Makes HTTP requests to Aquarium and returns JSON.

    This class should be generally
    obscured from Trident user so that users cannot make arbitrary requests to an Aquarium server and get sensitive
    information (e.g. User json that is returned contains api_key, password_digest, etc.) or make damaging posts.
    Instead, a SessionInterface should be the object that makes these requests.
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
    def _create_session_json(login, password):
        return {
            "session": {
                "login": login,
                "password": password
            }
        }

    # TODO: encrypt the header, store key in separate file (not accessible after pip install)
    def _login(self, login, password):
        """ Login to aquarium and saves header as a requests.Session() """
        session_data = self.__class__._create_session_json(login, password)
        res = None
        try:
            res = requests.post(os.path.join(self.aquarium_url, "sessions.json"),
                                json=session_data, timeout=self.timeout)
        except requests.exceptions.MissingSchema as e:
            raise TridentLoginError("Aquairum URL {0} incorrectly formatted. {1}".format(
                self.aquarium_url, e.args[0]))
        except requests.exceptions.ConnectTimeout as e:
            raise TridentTimeoutError("Aquarium took too long to respond during login. Make sure the url "
                                      "{} is correct. Alternatively, use Session.set_timeout to increase"
                                      "the request timeout.".format(self.aquarium_url))
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

    @to_json
    def post(self, path, json_data=None, timeout=None, **kwargs):
        """ Makes a post request to the session """
        if timeout is None:
            timeout = self.timeout
        return self._requests_session.post(os.path.join(self.aquarium_url, path), json=json_data, timeout=timeout,
                                           **kwargs)

    @to_json
    def put(self, path, json_data=None, timeout=None, **kwargs):
        """ Makes a put request to the session """
        if timeout is None:
            timeout = self.timeout
        return self._requests_session.put(os.path.join(self.aquarium_url, path), json=json_data, timeout=timeout,
                                          **kwargs)

    @to_json
    def get(self, path, timeout=None, **kwargs):
        """ Makes a get request to the session """
        if timeout is None:
            timeout = self.timeout
        return self._requests_session.get(os.path.join(self.aquarium_url, path), timeout=timeout ** kwargs)

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__, self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()
