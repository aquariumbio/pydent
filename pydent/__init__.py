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

from .__version__ import info
__version__ = info['version']
__title__ = info['name']
__author__ = info['authors']
__homepage__ = info['homepage']
__repo__ = info['repository']