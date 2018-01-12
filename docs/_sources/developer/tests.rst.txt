Tests
=====

Tests are written to run with pytest.

To run tests, first install trident's dependencies:

.. code::

    make

To run tests, run:

.. code::

    make tests


Test Coverage
-------------

Covering all of the models and endpoints for Trident is very difficult.
Tests coverage is not 100%.

For the most part, the `Marshaller`, `utilities`, `aqhttp`, `aqsession`, and
`baseclass` have near 100% coverage.

For testing of specific Aquarium models, tests are found in
'tests/test\_models/models.' Many of these model tests use 'monkeypatch'
to *intercept* requests and return expected information.
Writing these tests take a long time and so not all model tests are comprehensive.

Note JV 12/13/17: There are likely several better options
for running http request tests:
* HTTPretty https://github.com/gabrielfalcao/HTTPretty - convient methods to
intercept requests, similar to Ruby's FakeWeb
* VCRpy https://github.com/kevin1024/vcrpy - which has the capacity to *record*
requests and intercept http requests to the recorded version of the requests.

Testing with live and fake connections
--------------------------------------

In 'tests/conftest.py' two fixtures are defined `fake_session` and
`session.` `fake_session` contains a fake AqSession in which the
login information has been faked. `session` contains a potentially
live connection to Aquarium using login information located in
'tests/secrets/config.json.secret'

Though we should not run tests against a production or nursery server,
to run live tests with an Aquarium server, replace the
`tests/secrets/config.json.secret.template` and a new
`tests/secrets/config.json.secret` containing your login information

.. code-block:: JSON

    {
        "login": "yourlogin",
        "password": "password",
        "aquarium_url": "http://aquarium.org"
    }
