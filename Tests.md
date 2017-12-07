# Tests

Tests are written for using pytest.
To install [pytest](https://docs.pytest.org/en/latest/getting-started.html):

```bash
pip install -U pytest
```

To run the tests, simply run the following:

```bash
cd trident  # cd to the trident directory
pytest tests
```

## Test Coverage

Covering all of the models and endpoints for Trident is very difficult.
Tests coverage is not 100%.

For the most part, the Marshaller, utilities, aqhttp, aqsession, and
baseclass have near 100% coverage.

For testing of specific Aquarium models, tests are found in 'tests/test_models/models.'
Many of these model tests use 'monkeypatch' to *intercept* requests and return expected
information. Writing these tests take a long time and so not all model tests are comprehensive.

## Testing with live and fake connections

In 'tests/conftest.py' two fixtures are defined `fake_session` and
`session.` `fake_session` contains a fake AqSession in which
the login information has been faked. `session` contains a potentially
live connection to Aquarium using login information located in 'tests/secrets/config.json.secret'

Though we should not run tests against a production or nursery server,
to run 'live' tests with an Aquarium server, replace the 'tests/secrets/config.json.secret.template'
and a new 'tests/secrets/config.json.secret' containing your login information

```
{
    "login": "yourlogin",
    "password": "passwrod",
    "aquarium_url": "http://aquarium.org"
}
```
