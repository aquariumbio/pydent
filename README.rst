Trident: Aquarium API Scripting
===============================

`CircleCI <https://circleci.com/gh/klavinslab/trident/tree/master>`__
`PyPI version <https://badge.fury.io/py/pydent>`__

Trident is the python API scripting for Aquarium.

1. `Installation <docsrc/user/installation.rst>`__ - how to install
   pydent
2. `Examples <docsrc/user/examples.rst>`__ - example usages
3. `Contributing <docsrc/developer/contributing.rst>`__ - contributing
   and developer notes
4. `API Notes <docsrc/developer/api_notes.rst>`__ - notes on
   pydent/Aquarium models
5. `Tests <docsrc/developer/tests.rst>`__ - testing notes

Note: the initial version is tagged as ``v0.0.1-initial``, but is no
longer being developed.

Documentation
-------------

`API documentation can be found here at
klavinslab.org/trident <http://www.klavinslab.org/trident>`__

Requirements
------------

-  Python > 3.4
-  An Aquarium login

Quick installation
------------------

Pydent can be installed using ``pip3``

::

       pip3 install pydent

or upgraded using

::

       pip3 install pydent --upgrade

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
