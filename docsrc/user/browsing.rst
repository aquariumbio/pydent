Browsing using Trident
======================

Trident provides a browser class to help browse through Inventory.
Samples can be searched via regular expressions, close-matches, or by sample properties.

.. code::

    from pydent import AqSession
    from pydent.browser import Browser

    session = AqSession("login", "password", 'http://123.23.4.3')

    browser = Browser(session)

    # perform a regex search of samples containing 'gfp'
    gfp_samples = browser.search(".*GFP.*")

    # perform a regex search of samples containing 'pGFP', without ignoring case
    GFP_sample = browser.search(".*GFP.*", ignore_case=False)

    # perform a regex search of all Plasmids containing 'pGFP', without ignoring case
    gfp_fragments = browser.search(".*GFP.*", ignore_case=False, sample_type='Plasmid')

The browser can also find approximately close matches for a given string:

.. code::

    close_matches = browser.close_matches("pMOD8-pGRR-W8")

Samples can also be filtered by their sample properties:

.. code::

    samples = browser.search(".*mCherry.*", sample_type="Fragment")

    filtered_samples = browser.filter_by_sam