import json
import os
import re

import requests
from pillowtalk import SessionManager


def to_json(fxn):
    def wrapper(*args, **kwargs):
        r = fxn(*args, **kwargs)
        return r.json()

    return wrapper


# TODO: is mixing http with the session manager confusing?
class AqHTTP(object):
    def __init__(self, login, password, aquarium_url, name=None):
        self.login = login
        self.password = password
        self.aquarium_url = aquarium_url
        self.name = name
        self._session = None
        self._login()

    def _create_session(self):
        return {
            "session": {
                "login": self.login,
                "password": self.password
            }
        }

    def _login(self):
        """ """
        session_data = self._create_session()
        r = requests.post(os.path.join(self.aquarium_url,
                                       "sessions.json"), json=session_data)
        headers = {"cookie": self.__class__.__fix_remember_token(
            r.headers["set-cookie"])}
        self._session = requests.Session()
        self._session.headers.update(headers)

    @staticmethod
    def __fix_remember_token(h):
        parts = h.split(';')
        rtok = ""
        for c in parts:
            cparts = c.split('=')
            if re.match('remember_token', cparts[0]):
                rtok = cparts[1]
        return "remember_token=" + rtok + "; " + h

    @to_json
    def post(self, path, json=None, **kwargs):
        return self._session.post(os.path.join(self.aquarium_url, path), json=json, **kwargs)

    @to_json
    def put(self, path, json=None, **kwargs):
        return self._session.put(os.path.join(self.aquarium_url, path), json=json, **kwargs)

    @to_json
    def get(self, path, **kwargs):
        return self._session.get(os.path.join(self.aquarium_url, path), **kwargs)

    @to_json
    def put(self, path, json=None, **kwargs):
        return self._session.put(os.path.join(self.aquarium_url, path), json=json, **kwargs)

    def dump(self):
        session = self.__class__._session
        session_name = self.__class__.session_name()
        return {
            session_name: {
                "login": session.login,
                "password": session.password,
                "aquarium_url": session.aquarium_url
            }
        }

    def __repr__(self):
        return "<{}({}, {})>".format(self.__class__.__name__, self.login, self.aquarium_url)

    def __str__(self):
        return self.__repr__()


class AqSession(SessionManager):
    """ An aquarium session. Inherits SessionManager, which is a class based on the Borg-idiom """

    def create(self, login, password, aquarium_url, session_name=None):
        aqhttp = AqHTTP(login, password, aquarium_url, name=session_name)
        self.register_connector(aqhttp, session_name=session_name)

    def create_from_json(self, json_config):
        if "login" in json_config:
            self.create(**json_config)
        else:
            for session_name, session_config in json_config.items():
                self.create(**session_config, session_name=session_name)

    def create_from_config_file(self, path_to_config):
        with open(os.path.abspath(path_to_config)) as f:
            config = json.load(f)
            self.create_from_json(config)

    def __repr__(self):
        return "<{}({}: {})>".format(self.__class__.__name__, self.session_name, self.session)

    def __str__(self):
        return self.__repr__()
