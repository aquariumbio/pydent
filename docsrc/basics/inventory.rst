.. _inventory:

Inventory Management
====================
TBD here we describe the difference components of the Aquarium LIMS system
and the control offered by Trident.

Creating new samples
--------------------

.. code-block:: python

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast_instance = yeast_strain.new(
        name='my new yeast',
        description='This is the CEN.PK2 strain integrated with X at locus Y',
        project='Grant XNY Preproposal',
        properties={
            ...properties here
        }
    )

Updating sample properties
--------------------------

Update properties using the `update_properties` method and
providing a dictionary.

.. code-block:: python

    yeast_instance.update_properties({
        'QC Primer1': session.Sample.find(1),
        'QC_length': 1332
    })


Creating new items
------------------
TBD here we showcase how to create new items

Creating new collections
------------------------
TBD here we showcase how to create new multi-part collections, such
as 96-well plates.

Saving inventory
----------------
TBD here we showcase how to save inventory to Aquarium