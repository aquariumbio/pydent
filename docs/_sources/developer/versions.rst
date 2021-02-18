pydent change log
=================

1.0.3
-----

**2020-09-09T22:17:51.082004** Add handling of Krill libraries

.. _section-1:

1.0.2
-----

**2020-07-13T11:26:44.038874** Add tests to operation type.

.. _section-2:

1.0.1
-----

**2020-07-13T11:18:08.599254** Add tests to operation type.

.. _section-3:

1.0.0
-----

**2020-06-18T19:42:47.055781** Make release 1.0.0 from 0.1.0alpha

0.1.5a23
--------

**2020-05-19T10:09:04.242576** updates to AQL

-  ``query`` key changed to ``__query__`` key

0.1.5a21
--------

**2020-05-13T08:32:18.023349** Correction

-  removed print statement from ``pydent.save_inventory``

0.1.5a20
--------

**2020-04-26T10:52:22.897648** new features (AQL)

-  AQL: add ``__options__.pageSize`` to AQL schema

0.1.5a19
--------

**2020-04-25T19:58:33.514625** new features

-  Serialization: ``model.dump(include_uri=True)`` will return a unique
   URI for the model upon dump
-  Serialization: ``model.dump(include_model_type=True)`` will return
   the model class name upon dump
-  AQL: ``__as__`` key was removed from AQL query scheme. To dump JSON,
   add the ``__json__`` key to the top level.
-  AQL: ``__json__`` will, by default, dump **uri** and **model**
   attributes. These option can be changed by setting ``__json__`` =
   ``{"include_uri": false, "include_model_type": false}``

0.1.5a18
--------

**2020-03-15T14:19:15.948876** MIT License

0.1.5a17
--------

**2020-02-20T11:09:02.777062** bug fix

-  sample.save checks for required properties

0.1.5a16
--------

**2020-02-16T14:36:27.391598**

-  Added complex query method ``session.query`` and corresponding query
   schema.
-  Fixes to session.browser.where

0.1.5a15
--------

**2020-02-14T13:30:48.952836** bug fixes

-  several bug fixes related to setting FieldValue properties
-  ``Planner.add_from_template`` will add operations from a template to
   this Planner
-  ``Planner.copy`` has been fixed

0.1.5a14
--------

**2020-02-14T13:15:38.789723** Ω

.. _section-4:

0.1.5
-----

**2019-12-13T00:15:30.557477** 0.1.5a14

-  bug fixes
-  ``merge`` added to sample, which merge samples by name
-  ``save_inventory`` optionally merged samples

0.1.5a13
--------

**2019-12-12T23:16:13.054507** features

-  save_inventory method to save Samples, Collections, Plans, and Items

0.1.5a12
--------

**2019-12-12T21:04:58.993258** bug fixes

-  Planner.optimize bug fixes

0.1.5a11
--------

**2019-12-12T20:57:28.457117** bug fixes

-  fixed bug in which data associations without an id would attempt to
   save to server
-  added method to delete data associations from Collection.parts
-  added explicit method to add associations to parts

0.1.5a10
--------

**2019-12-12T16:05:57.054929** New major features

-  ``Collection`` model completely reworked.
-  ``Collection`` now has multiple ‘views’ to view dat, including
   sample_id, sample, data_value, data_associations, part_associations,
   and parts.
-  ``Collection`` sample_ids and data_associations c can be updated
   using advanced indexing
-  ``Collection`` update now will automatically update DataAssociations
   along with the Collection itself
-  DataAssociator refactored and fixed
-  Items now automatically upddate their data associations upon save

0.1.5a9
-------

**2019-11-19T18:48:57.740353** slimmed dependencies

-  removed ``arrow``
-  removed ``pandas``
-  changed browser.samples_to_df to check if pandas is installed

0.1.5a8
-------

**2019-11-19T18:33:38.350971** bug fixes

-  fixes loggable class and adds tests
-  fixes issue with attribute access in session
-  fixes issue whe3re Plan.one() return None for Aquarium 2.7
-  Plan no longer includes wires on query

0.1.5a6
-------

**2019-08-08T14:52:14.631040**

0.1.5a5
-------

**2019-08-08T14:43:40.229011** bug fix

-  fixes bug with field values that have no operations when using
   planner.set_to_available_item

0.1.5a4
-------

**2019-08-08T14:37:26.698386** bug fix with setting available items

-  fixed RESTRICT_TO_ONE for item_preference in planner
-  added RESTRICT_TO_ONE_ON_SERVER that looks at all reserved items on
   the server

0.1.5a3
-------

**2019-08-06T14:42:09.748998** bug fixes

-  fixes find(id=0) bug that raised a mysterious error
-  session..all() no longer raises error when cache is being used

0.1.5a2
-------

**2019-07-28T13:08:07.331007** minor bug fixes

-  Fixed error that occurred when Planner and PlannerLayout had no
   operations
-  Added ‘using_verbose’ to session factory. Create a verbose session
   using ``session(using_verbose=True)``
-  Improved logging library. Logging library accessible via ‘.log’ as in
   ``session.log.info(<msg>)``
-  Traceback limit for logging can be set using
   ``session.log.set_tb_limit(<limit>)``

0.1.5a1
-------

**2019-07-26T08:46:10.461557** installation of keats

-  keats manager tool installation
-  remove warnings that occurred during plan.save() and plan.update()

0.1.5a
------

--------------

-  fixes a planner.open() bug

.. _a-1:

0.1.4a
------

--------------

-  fixes a planner.save() bug

.. _a-2:

0.1.3a
------

--------------

-  added pydent.login method, which returns an AqSession instance with
   option to input password securely. Useful for live demos.

.. _a-3:

0.1.2a
------

--------------

-  .. rubric:: Major changes
      :name: major-changes

-  Planner class - a convenience class creating and editing plans in
   Aquarium.

-  ``Browser`` - a convenience class for browsing Samples and other
   models. Includes caching and query bundling to reduce number of
   queries and increase script speed.

-  new queries (one, last, first)

-  removed requirement of Marshmallow serialization/deserialization
   dependency, replaced by faster code

-  Removed ``marshmallow`` as a serialization/deserialization library. A
   custom library is now used that avoids unnecessary field validation.
   As a result, model ``load`` and ``dump`` is many fold faster.

Minor changes
^^^^^^^^^^^^^

-  Continuous validation - Cannot set Nested/Relationship attributes to
   arbitrary values. E.g. ``sample_type.sample = 5`` will raise an
   Exception, but setting ``sample_type.sample = mysample`` will not.

   -  ``sample_type.sample = mysample`` will also automatically set the
      ``sample_id`` attribute, since this is defined in the HasOne
      relationship as an attribute_key. But setting
      ``sample_type.sample.id = 5`` will not change the ``sample_id``
      key.

-  setting ``None`` will no longer trigger a query attempt. In previous
   versions, a relationship whose value was set to ``None`` would
   intialize a query attempt anytime ``getattr`` accessed a model
   attribute, using round-about exception handling to avoid errors; this
   made it impossible to set a relationship attribute to ``None.`` Now,
   a query will only be initiated if the key does not exist in the
   models underlying data. This means that data received from Aquarium
   will be used as expected (i.e. setting ``{"sample": None}`` will not
   try to initiate a query next time ``model.sample`` is called).

   -  ``FieldValue.set_value`` now handles None values. In previous
      version, None values passed into set_field_value would be ignored,
      making it difficult to *reset* a FieldValue. For example
      ``field_value.set_value(sample=None)`` will now reset the sample
      value for the FieldValue instead of being ignored.

-  ``primary_key`` will return an ``id``. If ``id==None``, then the
   ``rid`` is returned (e.g. ``rid1023``)
-  ``HasOne`` relationship will automatically set the corresponding
   model reference when setting attributes. E.g.
   ``sample.sample_type = myst`` will also automatically set
   ``sample.sample_type_id = myst.id`` since this is defined in the
   ``HasOne`` field. Similar tracking is not implemented for other
   relationships.

Developer changes

-  ``poetry`` https://poetry.eustace.io/ now used as the package
   manager, replacing *pipenv*
-  vcrpy\` is used to cache and store queries for deterministic testing.
-  Improved documentation.
