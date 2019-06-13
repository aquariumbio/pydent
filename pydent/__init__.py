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
from pydent._version import __version__, __title__, __author__, __homepage__, __repo__
