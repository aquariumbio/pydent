Browsing using Trident
======================

Trident provides a browser class to help browse through Inventory.
Samples can be searched via regular expressions, close-matches, or by sample properties.
As of 10/2018, these types of searching capabilities are not implemented in the
Aquarium Sample Browser GUI and can only be accessed through Trident.

A new Browser can be initialized by passing in a AqSession object:

.. code-block::

    from pydent import AqSession
    from pydent.browser import Browser

    session = AqSession("login", "password", 'http://123.23.4.3')
    browser = Browser(session)

Basic Browsing
--------------

Basic regular expression searches of samples by using the 'search' method:

.. code-block::

    # perform a regex search of samples containing 'gfp'
    gfp_samples = browser.search(".*GFP.*")

Additional flags can be passed into the regex search to narrow the search:

.. code-block::

    # perform a regex search of samples containing 'pGFP', without ignoring case
    GFP_sample = browser.search(".*GFP.*", ignore_case=False)

    # perform a regex search of all Plasmids containing 'pGFP', without ignoring case
    gfp_fragments = browser.search(".*GFP.*", ignore_case=False, sample_type='Plasmid')

Similarly, the browser can also find approximately close matches for a given string:

.. code-block::

    close_matches = browser.close_matches("pMOD8-pGRR-W8")
    [s.name for s in close_matches]
    # ['pMOD8A-RGR-W8', 'pMOD8-pGALz4-RGR-W8', 'pMOD8-pGALZ4-URGR-W8']

Once found, list of samples can also be filtered by their sample properties.
For example, we can find all of the primers containing "mcherry" that have a
*T Anneal* greater than 64:

.. code-block::

    primers = browser.search(".*mcherry.*", sample_type="Primer")
    browser.filter_by_field_value_properties(primers, "name = 'T Anneal' AND value > 64")

As you can see, there is a SQL-like style to the query. This same style can be applied directly
to where statements as well:

.. code-block::

    session.FieldValue.where("name = 'T Anneal' AND value > 64")

Browser Scope
-------------

The model scope of the browser can also be changed so that many of the methods
used in Sample, can be applied to other models (such as Operations or OperationTypes).
The following example finds protocols that look similar to "Fragment Analyzing"

.. code::

    browser.set_model("OperationType")
    ots = browser.close_matches("Fragment Analyzing")
    [ot.name for ot in ots]
    # ['Fragment Analyzing', 'Fragment Analyzing (EL)', 'Fragment Analyzing']


Making fast queries
-------------------

Complex model relationships can be queried very quickly. The following example retrieves
any data_association attached to an item whose sample has a name that matched 'mcherry'.

.. code-block::

    samples = browser.search(".*mCherry.*", sample_type="Fragment")
    items = browser.retrieve(samples, 'items')
    data_associations = browser.retrieve(items, 'data_associations')

    """
    searched:
        123 samples
        871 items
        477 data associations
        8.9 seconds using 5 queries
    """

The 'retrieve' function will also automatically cache the results into the model so
they may be accessed later:

.. code-block::

    samples = browser.search(".*mCherry.*", sample_type="Fragment")
    browser.retrieve(samples, 'items')

    samples[0].items  # already cached from 'retrieve'

Avoid using too many queries (N+1 problem)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TLDR; **AVOID FOR LOOPS** *Use browser.retrieve whenever possible to
avoid making unnecessary requests*

With the ease of making query requests in trident, it can be
easy to forget that each query puts a load on the online Aquarium server.
Poorly written Python code that makes many trident queries can translate into global
Aquarium slowdowns for everyone using that server.

Generally, you should write your code to minimize the number of queries made. For example,
the following code retrieves all items from a list of samples, and then retrieves all data
associated with those items. When this example was run, 100 samples, 871 items, and 471 data_associations
were retrieved in just 4 seconds:

.. code-block::

    # GOOD CODE (exactly 3 requests to server)
    ## 20 samples: completes in 0.8 seconds for 20 samples on AWS
    ## 100 samples: completes in 3.9 seconds for 100 samples on AWS

    items = browser.retrieve(samples, 'items') # 1 request to server
    data_associations = browser.retrieve(items, 'data_associations')  # 2 requests to server

Using a series of nested for loops that makes queries is an example of **exceptionally bad** code,
as in the following example:

.. code-block::

    # BAD CODE (makes N^3 requests to server)
    ## 20 samples: completes in >12 seconds for 20 samples on AWS
    ## 100 samples: completes > 60 seconds

    data = []
    for s in samples:
        for i in s.items:
            data += i.data_associations

Asynchrounous Requests
----------------------

As long as you are being mindful of the number of requests you are making,
trident provides methods for making parallel requests to speed up
your trident scripts.

The 'make_async' decorator located in 'pydent.utils' can make any function
asynchrounous, provided they use a list as its first argument and returns
a list.

'make_async' takes in a 'chunk_size' argument, which will divide the first argument
(a list) into a number of chunks of size 'chunk_size' and run
each chunk simulatenously. The value that is returned is the concatenation of all of
the lists returned by each chunk once all chunks have been completed.

For example, the following gets samples based on their id and will split the ids
into chunks of size 50. This outperforms (only slightly) an equivalent
non-asynchronous method. While the performance improvement is slight in this example,
longer running processes can have great improvements by running them asynchrounously.
You may have to experiment with the 'chunk_size' to get the best performance.

.. code-block::

    from pydent.utils import make_async

    @make_async(50, progress_bar=True)
    def get_samples_async(sample_ids):
        return session.Sample.find(sample_ids)

    def get_samples(sample_ids):
        return session.Sample.find(sample_ids)

Note that it is not currently possible to use a async method nested within a async method.
An exception will be raised if this occurs. The planner, for example, already uses async methods.