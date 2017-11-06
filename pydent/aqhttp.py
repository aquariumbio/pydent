import json
import os
import re

import requests

from pydent.exceptions import TridentRequestError, TridentLoginError


def to_json(fxn):
    """ returns formated the request response as a JSON.
    Throws exception if response is not formatted properly."""
    def wrapper(*args, **kwargs):
        ret = fxn(*args, **kwargs)
        try:
            return ret.json()
        except json.JSONDecodeError:
            raise TridentRequestError(
                "Response is not JSON formatted. Trident is probably not properly "
                "connected to the server. Verify login credentials.")

    return wrapper


class AqHTTP(object):
    """ Defines a session/connection to Aquarium """

    def __init__(self, login, password, aquarium_url):
        """
        Initializes an aquarium session with login, password, server combination

        :param login: Aquarium login
        :type login: basestring
        :param password: password
        :type password: basestring
        :param aquarium_url: aquarium url to the server
        :type aquarium_url: basestring
        """
        self.login = login
        self.password = password
        self.aquarium_url = aquarium_url
        self._session = None
        self._login()

    def _create_session_json(self):
        return {
            "session": {
                "login": self.login,
                "password": self.password
            }
        }

    def _login(self):
        """ Login to aquarium and saves header as a requests.Session() """
        session_data = self._create_session_json()
        res = None
        try:
            res = requests.post(os.path.join(self.aquarium_url,
                                         "sessions.json"), json=session_data)
        except requests.exceptions.MissingSchema as e:
            raise TridentLoginError("Aquairum URL {0} incorrectly formatted. {1}".format(self.aquarium_url, e.args[0]))
        headers = {"cookie": self.__class__.fix_remember_token(
            res.headers["set-cookie"])}
        self._session = requests.Session()
        self._session.headers.update(headers)

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
    def post(self, path, json_data=None, **kwargs):
        """ Makes a post request to the session """
        return self._session.post(os.path.join(self.aquarium_url, path), json=json_data, **kwargs)

    @to_json
    def put(self, path, json_data=None, **kwargs):
        """ Makes a put request to the session """
        return self._session.put(os.path.join(self.aquarium_url, path), json=json_data, **kwargs)

    @to_json
    def get(self, path, **kwargs):
        """ Makes a get request to the session """
        return self._session.get(os.path.join(self.aquarium_url, path), **kwargs)

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__, self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()
