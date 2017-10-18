# import pytest
from pydent.aq import *

def test_login():

    Session.create_from_config("secrets/config.json")