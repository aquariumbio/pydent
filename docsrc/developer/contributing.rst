Contributing
============

pipenv and installation notes
-----------------------------

It is recommended you install Trident using pipenv.
`Pipenv <https://docs.pipenv.org/>`__ is now the officially
recommended Python packaging tool from Python.org. This avoids low level
management of pip and virtualenv.

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

Before making any changes, install the git hooks to help prevent changes to the 
docs directory, which contains generated documentation files:

::

    make hooks

Notes on Pipfile.lock
~~~~~~~~~~~~~~~~~~~~~

Please do not commit changes to your Pipfile.lock unless you are sure
those dependencies are the ones you want people using in their version
of trident.

Notes on IDEs + pipenv
~~~~~~~~~~~~~~~~~~~~~~

IDEs often default to a particular python interpreter, meaning they can
bypass the pipenv environment for trident. If running tests through tox
or py.tests in your IDE, make sure to set your interpreter to the python
located in your ~/.virtualenv/[project]/

Which environment you are using can be found by running
``pipenv --venv``

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
documents located in ``docsrc``. Documentation will be built in ``docs``.

``make doctest``
~~~~~~~~~~~~~~~~

Runs api tests contained in the ``docsrc``.

``make testdeploy``
~~~~~~~~~~~~~~~~~~~

Deploys release to PyPi test server


Documentation
-------------

Documentation is pulled from the code to create the
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

If a method returns a value use the ``:returns`` tag to describe the returned 
values, and if it throws an exception use the ``:raises`` tag to list the 
exception classes thrown.

Making a Release
----------------

1. Make sure tests clear

::

    make test
    make doctest

2. Update documentation

::

    make hooks
    make docs

3. Commit changes to github.
4. Make a release on github.


    make testdeploy

Then commit on github. Make a new release on github. Release to PyPi using:

::

    make deploy
