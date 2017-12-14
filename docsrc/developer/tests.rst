Tests
=====

Tests are written for using pytest. To run tests, move
into trident's root directory and run

.. code::

    make
    make test

Test Coverage
-------------

Covering all of the models and endpoints for Trident is very difficult.
Tests coverage is not 100%.

For the most part, the Marshaller, utilities, aqhttp, aqsession, and
baseclass have near 100% coverage.

For testing of specific Aquarium models, tests are found in
'tests/test\_models/models.' Many of these model tests use 'monkeypatch'
to *intercept* requests and return expected information. Writing these
tests take a long time and so not all model tests are comprehensive.

Note JV 12/13/17: We may want to consider using vcr https://github.com/kevin1024/vcrpy
which has the capacity to *record* requests and intercept http requests
to the recorded version of the requests. As of now, I don't have the time
to do this.

Testing with live and fake connections
--------------------------------------

In 'tests/conftest.py' two fixtures are defined ``fake_session`` and
``session.`` ``fake_session`` contains a fake AqSession in which the
login information has been faked. ``session`` contains a potentially
live connection to Aquarium using login information located in
'tests/secrets/config.json.secret'

Though we should not run tests against a production or nursery server,
to run 'live' tests with an Aquarium server, replace the
'tests/secrets/config.json.secret.template' and a new
'tests/secrets/config.json.secret' containing your login information

::

    {
        "login": "yourlogin",
        "password": "passwrod",
        "aquarium_url": "http://aquarium.org"
    }
