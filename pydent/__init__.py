"""

.. module:: pydent

Submodules
==========

.. autosummary::
    :toctree: _autosummary

    aqhttp
    aqsession
    base
    exceptions
    interfaces
    models
    relationships
    browser
    planner
    marshaller
    utils

"""

# without nest_asyncio, Jupyter notebooks will crash if an async method is used
import nest_asyncio

nest_asyncio.apply()

from .aqsession import AqSession
from .base import ModelBase, ModelRegistry
from .utils import pprint
from .browser import Browser
from .__version__ import __version__, __title__, __authors__, __homepage__, __repo__
import getpass


def login(user, url, password=None):
    """
    Create a new AqSession instance from login information.

    :param user: user login
    :type user: basestring
    :param url: server url
    :type url: basestring
    :param password: optional password. If left blank, a secure prompt will ask for the password.
    :type password: basestring | None
    :return: the session
    :rtype: AqSession
    """
    if password is None:
        return AqSession(user, getpass.getpass(), url)
    return AqSession(user, password, url)
