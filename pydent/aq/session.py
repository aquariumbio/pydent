import json
import os

from pydent.aq.aqhttp import AqHTTP
from pydent.aq.sessionmanager import SessionManager


class Session(SessionManager):
    """ Class for creating sessions """

    @classmethod
    def create(cls, login, password, aquarium_url, name=None):
        return cls.create_session(AqHTTP, login, password, aquarium_url, name=name)

    @classmethod
    def create_from_json(cls, json_config):
        if "login" in json_config:
            cls.create(**json_config)
        else:
            for session_name, session_config in json_config.items():
                cls.create(**session_config, name=session_name)

    @classmethod
    def create_from_config_file(cls, path_to_config):
        with open(os.path.abspath(path_to_config)) as f:
            config = json.load(f)
            cls.create_from_json(config)
