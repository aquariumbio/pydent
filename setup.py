import os
import re
from distutils.core import setup

# about
__author__ = ''
__license__ = '?'
__package__ = "pydent"
__readme__ = "README"

tests_require = [
    'pytest',
    'pytest-runner',
    'python-coveralls',
    'pytest-pep8'
]

install_requires = [
    "pillowtalk",
    "requests",
    "inflection"
]

classifiers = [],

# setup functions
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_property(prop, project):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
    if result:
        return result.group(1)
    else:
        raise RuntimeError("Unable to find property {0} in project \"{1}\".".format(prop, project))

def get_version():
    try:
        return get_property("__version__", __package__)
    except RuntimeError as e:
        raise RuntimeError("Unable to find __version__ string in project \"{0}\"".format(__package__))

# setup
setup(
        name=__package__,
        version=get_version(),
        packages=["pydent", "pydent/aq"],
        url='https://github.com/klavinslab/trident',
        license=__license__,
        author=__author__,
        author_email='',
        keywords='',
        description='',
        long_description=read(__readme__),
        install_requires=install_requires,
        python_requires='>=3.4',
        tests_require=tests_require,
)
