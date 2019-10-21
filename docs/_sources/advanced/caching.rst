.. _structured_queries:

Structured queries
==================

.. versionadded:: 0.1
    the Browser class provides structured queries.

Trident provides a way to make structured and efficient model queries using the
new :class:`Browser <pydent.browser.Browser>` class. The best way to utilize
this new class, is to spawn a new session using a cache. A brief overview of
the available API is below:

.. code-block:: python

    with session.with_cache(timeout=60) as sess:
        # sess is a new AqSession
        # perform code inside of here

        # use the session to find the last 50 samples
        # attach those samples automatically to a cache
        samples = sess.browser.last(50, 'Sample')

        # inside the 'with' statement, this is equivalent to...
        samples = sess.Sample.last(50)

        # returns all Samples in the cache
        samples_from_cache = sess.browser.get('Sample')
        assert samples == samples_from_cache

        # efficiency collects all of the samples' 'sample_type' attr
        sample_types = sess.browser.get('Sample', 'sample_type')

        # optionally, we can provide specific models
        sample_types2 = sess.browser.get(samples[:10], 'sample_type')

        # efficiently collect do a nested query finding the
        # all of the models related to items, samples, sample_types, field_types, and
        # field_values, and object types

        sess.last('Item', 50)
        sess.browser.get('Item', {
            'sample': {
                'sample_type': [],
                'field_values': {'sample', 'field_type'}  # can be a list, set, tuple, etc.
            },
            'object_type': 'field_type'
        })

.. _cache:

Speeding up queries
===================

Session objects can automatically cache model results to greatly
speed up data mining. It does this using the `Browser` class, which
is stored in the `.browser` attribute of the session.

To begin, lets grab a normal AqSession instance.

.. code-block:: python

    from pydent import AqSession

    session = AqSession('mylogin', 'mypass', 'myurl.org')

By default, the cache is turned off. We can see this by printing off
the browser

.. code-block:: python

    if session.browser:
        print(session.browser.model_cache)
    else:
        print("No browser")

Lets turn on the cache, which initializes the browser

.. code-block:: python

    session.using_cache = True
    s = session.Sample.one()
    print(session.browser.model_cache.keys())

.. code-block:: python

    {"Sample": {12355: <Sample>}}

We should now see that the queries model has been cached in the browsers dictionary. Now, next time
we attempt to retrieve the sample, we should preferentially retrieve from the model_cache.


.. code-block:: python

    s2 = session.Sample.find(s.id)
    assert id(s) == id(s2)

Due to how models inherit their sessions from other models, queries made
via attribute relationships are also attached to the model_cache


.. code-block:: python

    s.sample_type
    s.sample_type.field_types
    assert 'SampleType' in session.browser.model_cache
    assert session.browser.model_cache['SampleType']
    assert 'FieldType' in session.browser.model_cache
    assert session.browser.model_cache['FieldType']

Temporary Sessions
------------------

Of course, caching may not always be desirable, as in the case
of making server updates. If we only ever pulled from our local
cache, we would be unable to see any updates on the server. In this
case, we may want to create a **temporary** cache, perform optimized
queries, and then return the models. To do this, we can use the new
temporary session API.

Conviniently, sessions themselves are session factories. We can
spin off new sessions with new properties using existing sessions.

.. code-block:: python

    mynewsession = session()

We can instantiate a session with new properties. For example, spinning
off a session with `using_cache=True`

.. code-block:: python

    nocache = session(using_cache=False)

We can also instantiate sessions with requests turned off or
with new timeouts or sessions that inherith the model cache.

.. code-block:: python

    increasetimeout = session(timeout=60)
    norequests = session(using_requests=False)
    inheritcache = session(using_models=True)

However, this can become troublesome if we have many different sessions
attached to many different models. To keep everything tidy, we can use the
`with` api of the session.


.. code-block:: python

    with session(using_cache=True) as sess:
        samples = sess.Sample.last(100)
        sess.browser.get(samples, 'sample_type')

        # in the 'with' statement, models inherit the temporary session
        assert samples[0].session is not session
        assert samples[0].session is sess

    # upon exiting the with statement, models return
    # to the original session.
    assert samples[0].session is session

Two convinience methods have been implemented to use cache and
turn off requests. You can use these `with` nested with statements as well:

.. code-block:: python

    with session.with_cache() as sess1:
        samples = sess1.Sample.last(10)
        with sess1.with_request_off() as sess2:
            sess2.find(samples[0].id)


Optimized queries
-----------------

We can perform optimized queries using the browser's `get` method. This allows
us to pull model relationships very efficiently from the server. Under the hood,
Trident is using knowledge of model relationships to efficiently optimize queries
sent to the server and preferentially using a local model cache.

Optimized queries can increase data mining speed by up to 5-fold.
Here the optimized method (#4) is compared with nested requests (#1 and #2) and
server side deserialization (#3).

.. image:: _static/benchmark/histogram-test_query_benchmark.svg
    :width: 100 %

Below is an example of retrieve nested model information for many plans:

.. code-block:: python

    with session.with_cache() as sess:
        plans = sess.Plan.last(50)

        sess.browser.get(plans, {
            "operations": {
                "field_values": {
                    "sample": "sample_type",
                    "item": 'object_type',
                    'field_type': []
                }
            }
        }

    # now data is cached in the plans!
    for p in plans:
        for op in p.operations:
            for fv in op.field_values:
                print(fv.sample.name)
