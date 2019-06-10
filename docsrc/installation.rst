Installation
============

Requirements
------------

1. pip3

2. python3.6 or greater

Installation
------------

Pydent can be install using pip:

::

   pip3 install pydent --upgrade

To use trident, you'll need an Aquarium login, password, and url

::

    from pydent import AqSession

    session = AqSession("user", "password", "http://you.aquarium.url")
