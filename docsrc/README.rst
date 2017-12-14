Trident: Aquarium API Scripting
===============================

Trident is the python API scripting for Aquarium.

1. `Examples <docsrc/user/examples.md>`__
2. `API Notes <docsrc/developer/api_notes.md>`__
3. `Tests <docsrc/developer/tests.md>`__
4. `Updating Documentation <docsrc/developer/creating_docs.md>`__

API documentation is located in ``docs/index.html``.

Requirements
------------

-  Python > 3.4
-  an Aquarium login

Installation
------------

1. Clone or download `this
   repo <https://github.com/klavinslab/trident>`__
2. cd to directory containing trident
3. run ``pip install .`` or ``pip install . --upgrade``

Basic Usage
-----------

Logging in
~~~~~~~~~~

.. code:: python

    from pydent import AqSession

    # open a session
    mysession = AqSession("username", "password", "www.aquarium_nursery.url")

    # find a user
    u = mysession.User.find(1)

    # print the user data
    print(u)

Models
~~~~~~

.. code:: python

    print(mysession.models)

Finding models
^^^^^^^^^^^^^^

-  By name: ``nursery.SampleType.find_by_name("Primer")``

-  By ID: ``nursery.SampleType.find(1)``

-  By property: ``nursery.SampleType.where({'name': 'Primer'})``

-  All models: ``nursery.SampleType.all()``

Getting nested data
^^^^^^^^^^^^^^^^^^^

.. code:: python

    # samples are linked to sample_type
    primer_type = mysession.SampleType.find_by_name("Primer")
    primers = primer_type.samples

    # and sample type is linked to sample
    p = primers[0]
    print(p.sample_type)

Available nested relationships
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    primer_type = mysession.SampleType.find(1)
    print(primer_type.relationships)
