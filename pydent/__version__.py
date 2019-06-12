# TRIDENT
import configparser
from os.path import join, abspath, dirname

here = dirname(abspath(__file__))


config = configparser.ConfigParser()
config.read(join(here, "..", "pyproject.toml"))

info = config["tool.poetry"]
