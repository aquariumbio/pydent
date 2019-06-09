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

from .__version__ import __description__, __author__, __version__, __url__, __title__, __pypi__
from .aqsession import AqSession
from .base import ModelBase, ModelRegistry
from .utils import pprint
