import os
import re
from pillowtalk import SessionManager
import requests
import json

def to_json(fxn):
    def wrapper(*args, **kwargs):
        r = fxn(*args, **kwargs)
        return r.json()

    return wrapper


class AqHTTP(SessionManager):
    def __init__(self, login, password, aquarium_url):
        self.login = login
        self.password = password
        self.home = aquarium_url
        self.session = None
        self._login()

    def _create_session(self):
        return {
            "session": {
                "login"   : self.login,
                "password": self.password
            }
        }

    def _login(self):
        """ """
        session_data = self._create_session()
        r = requests.post(os.path.join(self.home, "sessions.json"), json=session_data)
        headers = {"cookie": AqHTTP.__fix_remember_token(r.headers["set-cookie"])}
        self.session = requests.Session()
        self.session.headers.update(headers)

    @classmethod
    def create_from_json(cls, json_config):
        if "login" in json_config:
            cls.create(**json_config)
        else:
            for session_name, session_config in json_config.items():
                cls.create(**session_config, session_name=session_name)

    @classmethod
    def create_from_config_file(cls, path_to_config):
        print(os.path.abspath(path_to_config))
        with open(os.path.abspath(path_to_config)) as f:
            config = json.load(f)
            cls.create_from_json(config)


    @staticmethod
    def __fix_remember_token(h):
        parts = h.split(';')
        rtok = ""
        for c in parts:
            cparts = c.split('=')
            if re.match('remember_token', cparts[0]):
                rtok = cparts[1]
        return "remember_token="+rtok+"; "+h

    @to_json
    def post(self, path, json=None, **kwargs):
        return self.session.post(os.path.join(self.home, path), json=json, **kwargs)

    @to_json
    def put(self, path, json=None, **kwargs):
        return self.session.put(os.path.join(self.home, path), json=json, **kwargs)

    @to_json
    def get(self, path, **kwargs):
        return self.session.get(os.path.join(self.home, path), **kwargs)

    @to_json
    def put(self, path, json=None, **kwargs):
        return self.session.put(os.path.join(self.home, path), json=json, **kwargs)
