import os
import re
from distutils.core import setup

# about
__author__ = 'Justin Vrana, Eric Klavins, Ben Keller'
__license__ = ''
__package__ = "pydent"
__readme__ = "README.md"
__version__ = "0.0.2a"
__email__ = ''


tests_require = [
    'pytest',
    'pytest-runner',
    'python-coveralls',
    'pytest-pep8'
]

install_requires = [
    'inflection',
    'marshmallow'
]


# setup functions



here = os.path.abspath(os.path.dirname(__file__))
#
#
# about = {}
# with open(os.path.join(here, 'requests', '__version__.py'), 'r', 'utf-8') as f:
#     exec(f.read(), about)
with open(os.path.join(here, 'pydent', '__version__.py', 'r')) as f:
    print(f.read())

# setup
setup(
        name='pydent',
        version='0.1a',
        packages=["pydent", "pydent.session", "pydent.marshaller"],
        url='https://github.com/klavinslab/trident',
        license='',
        author='',
        author_email='',
        keywords='aquarium api',
        description='',
        install_requires=install_requires,
        python_requires='>=3.4',
        tests_require=tests_require,
)
