"""aqsession.py

This module defines the AqSession class, which is the main entry point for accessing
Trident's request methods. Multiple session instances can be created using a users
Aquarium login information. From there, the session instance is used to make http
requests (like finding models, updating plans, etc.)

AqSession creates SessionInterfaces which can make http requests to Aquarium but
does not itself make the requests.

Interfaces are accessed by:

(1) session.<ModelName> - access the model interface
(2) session.create - access the create interface
(3) session.update - access the update interface
"""

from pydent.session.aqhttp import AqHTTP
from pydent.marshaller import ModelRegistry
from pydent.session.interfaces import ModelInterface, CreateInterface, UpdateInterface
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit import prompt
# TODO: We want to prevent the user from accessing aqhttp
# TODO: Could store encrypted key in class that user doesn't have access to. Key would need to be passed to AqHTTP object in order to work...
# TODO: Or, aqhttp would only work with the session interface that created it somehow
# TODO: Should never be allowed to change the current s
class AqSession(object):
    """
    Holds a AqHTTP with login information. Creates SessionInterfaces for models.

    e.g.
        session1 = AqSession(username, password, aquairum_url)
        session1.User.find(1)
           <User(id=1,...)>
    """

    def __init__(self, login, password, aquarium_url, name=None):
        self.name = name
        self.__aqhttp = AqHTTP(login, password, aquarium_url)
        self.__current_user = None

    def set_timeout(self, timeout_in_seconds):
        """Sets the request timeout."""
        self.__aqhttp.timeout = timeout_in_seconds

    @classmethod
    def interactive(cls):
        confirm_register = False
        while not confirm_register:
            password = None
            confirm_password = None
            username = prompt('enter username: ')
            url = prompt('enter url: ')
            msg = ''
            while confirm_password is None or password != confirm_password:
                if msg:
                    print(msg)
                password = prompt('enter password: ', is_password=True)
                confirm_password = prompt('confirm password: ', is_password=True)
                msg = "passwords did not match!"
            confirm_register = confirm('Confirm registration for {}@{}? (y/n): '.format(username, url))
            print()
        print("username {} registered".format(username))
        login = dict(login=username, password=password, aquarium_url=url)
        return cls(**login)

    @property
    def current_user(self):
        if self.__current_user is None:
            self.__current_user = self.User.where(
                {"login": self.__aqhttp.login})[0]
        return self.__current_user

    @property
    def models(self):
        return list(ModelRegistry.models.keys())

    def __getattr__(self, item):
        if item == "create":
            return CreateInterface(self.__aqhttp, self)
        elif item == "update":
            return UpdateInterface(self.__aqhttp, self)
        elif item in ModelRegistry.models:
            return self.model_interface(item)
        return object.__getattribute__(self, item)

    # TODO: add other interfaces as well
    def __dir__(self):
        return super().__dir__() + list(ModelRegistry.models.keys())

    def model_interface(self, model_name):
        return ModelInterface(model_name, self.__aqhttp, self)
