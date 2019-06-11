Contributing
============

Running Tests
-------------

Tests are written to run with pytest.

To run tests, first install trident's dependencies:

.. code::

    make

To run tests, run:

.. code::

    make tests

To run doctests located in `user/examples`.

.. code::

    make doctest

Server vs local tests
~~~~~~~~~~~~~~~~~~~~~

Tests that **do not** access the server are located in `tests/test_pydent`.
Requests are turned off by default for any test within this directory. These tests will
not access the server and use a pytest fixture `fake_session` to perform Trident tests, as in
the following:

::

    def my_non_server_test(fake_session):
        s = fake_session.Sample.one()
        # do stuff with fake sample 's'


Tests that **do** access the server are located in `tests_with_server_and_cached_results`.
These tests will use the `tests_with_server_and_cached_results/secrets/config.json.secret` file
to login to a live server:

.. code-block:: JSON

    {
        "login": "Neptune",
        "password": "aquarium",
        "aquarium_url": "http://0.0.0.0:80"
    }

Please remember not to commit your login information.

Server tests use the `session` pytest fixture, as in the following:

::

    def my_sever_test(session):
        s = session.Sample.one()
        # do stuff with real sample 's'

Information on sessions and servers can be found in the `conftest.py` files within the `tests`
directory.

Request recording
`````````````````

By default, live requests are recorded automatically via
`VCRpy <https://vcrpy.readthedocs.io/en/latest/installation.html>`_

Information about each request is stored in a **fixtures/vcr_cassettes/*.yaml**
and retrieved on a as-needed basis.

You may turn off request recording using the following decorator. This may be necessary
if your test makes a server change:

::

    @pytest.mark.record_mode('no')
    def my_sever_test(session):
        s = session.Sample.one()
        # do stuff with real sample 's'

Installing dependencies
-----------------------

Trident uses `poetry <https://https://poetry.eustace.io/>`_ for installation and distribution.
Installation information is managed by `poetry` in the `pyproject.toml` file.
Please view the poetry documentation on how to install it.

::

    poetry add [name_of_dependency]

Dependencies can be install using

::

    poetry install

To open a virtual environment with the poetry installation, use either of the following:

::

    poetry shell

    poetry run [command]

Again, refer to the `poetry documentation <https://https://poetry.eustace.io/>`_ for further details.

Before making any changes, install the git hooks to help prevent changes to the
docs directory, which contains generated documentation files:

::

    make hooks

Making a Release
----------------

ToDo: write documentation on using poetry to publish to pypi