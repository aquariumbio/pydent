"""pydent."""
# without nest_asyncio, Jupyter notebooks will crash if an async method is used
import getpass

import nest_asyncio

from .__version__ import __authors__
from .__version__ import __homepage__
from .__version__ import __repository__
from .__version__ import __title__
from .__version__ import __version__
from .aqsession import AqSession
from .base import ModelBase
from .base import ModelRegistry
from .browser import Browser
from .inventory_updater import save_inventory
from .planner import Planner
from .utils import logger
from .utils import pprint

nest_asyncio.apply()


def login(user, url, password=None):
    """Create a new AqSession instance from login information.

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
