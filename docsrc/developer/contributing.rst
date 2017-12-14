Contributing
============

Submitting issues
-----------------

For now, just make an issue if something is wrong.

Making a pull request
---------------------

Information about how to fork and make a pull request will go here.

pipenv and installation notes
-----------------------------

It is recommended you install Trident using pipenv.
`**Pipenv** <https://docs.pipenv.org/>`__ is now the officially
recommended Python packaging tool from Python.org. This avoids low level
management of pip and virtualenv. See https://docs.pipenv.org/ for more
information.

To install a new dependency to trident, while in the trident root
directory:

::

    pipenv install [name_of_dependency]

To freeze the requirements to the ``Pipfile.lock`` file:

::

    pipenv lock

To install trident's dependencies to its virtual environment:

::

    pipenv install

To install trident's dependencies plus developer dependencies:

::

    pipenv install --dev

Makefile
--------

The ``Makefile`` contains entry points for running common tasks such as
installation of developer dependencies, testing, testing coverage,
updating documentation. These tasks will utilize the dependency
environment located in the ``Pipfile.lock`` For more information
regarding pipenv and Pipfile.lock, see https://docs.pipenv.org/.

A breakdown the current tasks are below.

``make``
~~~~~~~~

This command runs the ``init`` command and will essentially install
developer dependencies for trident.

``make test``
~~~~~~~~~~~~~

This will run all the pytests located in the ``tests`` folder. It will
also test the creation of the sphinx documentation.

These tests are governed by
`tox <https://tox.readthedocs.io/en/latest/>`__, a testing automation
package (see the ``tox.ini`` file)

``make coverage``
~~~~~~~~~~~~~~~~~

This will run testing coverage for the pydent directory.

``make pylint``
~~~~~~~~~~~~~~~

This will run pylint in the pipenv environment.

``make docs``
~~~~~~~~~~~~~

This will use sphinx (http://www.sphinx-doc.org/en/stable/) to
autogenerate documentation from trident's docstrings using source
documents located in ``docsrc.`` Documentation will be built in ``docs``

More commands?
~~~~~~~~~~~~~~

We will likely have more command such as updating the project, tagging a
release, etc.

Releases/Tagging
----------------

We haven't released anything yet. But when we do, some information about
making a release will go here.

Documentation
-------------

Documentation strings will be pulled from the code to create the
documentation using sphinx. Errors in the documentation will result in
errors when running the documentation tests, so please write
documentation correctly.

doc style
~~~~~~~~~

For most methods, classes, and modules, use the form:

.. code:: python


    def __init__(self, aqhttp, session):
    """
    Initializer for SessionInterface

    :param aqhttp: aqhttp instance for this interface
    :type aqhttp: AqHTTP
    :param session: session instance for this interface
    :type session: AqSession
    """

    self.aqhttp = aqhttp
    self.session = session

If documentation is obvious, use the short form of:

.. code:: python

    def add_numbers(x, y):
        """This adds two numbers together"""
        return x + y
