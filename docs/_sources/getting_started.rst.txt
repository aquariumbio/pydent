Getting Started
===============

Trident (also known as `pydent`) is the Python API to Aquarium, aa open-source
human-in-the-loop laboratory automation system that enables rapid,
flexible, and reproducible workflow development and execution. Unlike most other
automation systems, Aquarium embraces the practicality of humans in the laboratory, using codified human-readable instructions to automate lab operations.
You can learn more about it here: https://www.aquarium.bio/

Trident provide algorithmic access to a scientific laboratory running Aquarium.
It provides an interface for algorithms and computerized-agents
to interact the scientific laboratory, enticing the possibility engineering systems
that can not only learn from experimental data, but can actually schedule and run
its own experiments with little human intervention.

.. testsetup::

    import os
    import json
    from pydent import AqSession, models, ModelBase

    def config():
        """Returns the config dictionary for live tests."""
        dir = os.path.realpath('../tests')
        config_path = os.path.join(dir, "secrets", "config.json.secret")
        config = None
        with open(config_path, 'rU') as f:
            config = json.load(f)
        return config


    def session():
        """Returns a live aquarium connection."""
        return AqSession(**config())

    ModelBase.new_record_id = lambda: 1
    prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)

    session = session()


Logging into a session
~~~~~~~~~~~~~~~~~~~~~~

Session instances provide the main interface between your Python script
and various requests made to an Aquarium server.

To use trident, you'll need an Aquarium login, password, and url

::

    from pydent import AqSession

    session = AqSession("user", "password", "http://you.aquarium.url")

If we want to take a look at exactly what the session is doing, we can set verbose mode on:

.. code:: python

    session.set_verbose(True)

This produces many log files, so lets leave it off initially.


Models
~~~~~~

In Trident, scientific models are treated as first class objects. These objects
represent various aspects of most laboratories. These models include laboratory inventory such as

**Samples** -- laboratory entities (such as a `Plasmid` or *`E. coli`) that have chemical or biological properties

**Items** -- physical instantiations of a `Sample`, such as a specific tube of Plasmid or a particular
glycerol stock of an *E. coli* strain.

**Collections** -- multi-compartment items that can contain many samples (e.g a 96-well Plate)

**ObjectType** -- The type of container a collection/item possess (e.g. a small tube vs a large tube)

Samples, Items, and Collections comprise the inventory system of Trident/Aquarium. Items have a unique
id and a physical local associated with the lab. The biological/chemical properties are detailed by its
Sample. Further, Samples have specific types called SampleTypes which further constrain the types of
Samples there can be. For example, a yeast strain is one `SampleType` while a bacterial strain is another
`SampleType`. There may be many types of yeast strains in the inventory, each with their own specific properties
(e.g. genome sequence, antibiotic resistance). Each of these samples may have a myriad of different `Items`
in the lab of different `ObjectTypes`. The inventory relationships are depicted here:

.. image:: _static/Fig2_LIMS.png
    :width: 100 %

In addition to the inventory models, Trident/Aquarium has a protocol execution model as well:

**Operation** -- a scientific protocol that takes in some specified number inventory or parameters
and produces some other inventory

**Job** -- model representing actions taken during the execution of an `Operation` (dates, steps, etc.)

**Plans** -- a set of `Operations` connected in a graph that roughly represents a scientific experiment

**DataAssociation** -- a key/value pair associated with inventory, plans, or operations

**etc.**

.. image:: _static/Fig3_Planning.png
    :width: 100 %

To view all of the models available through Trident, run

.. testcode::

    from pydent.models import __all__
    print(__all__)

.. testoutput::

    ['Account', 'AllowableFieldType', 'Budget', 'Code', 'Collection', 'DataAssociation', 'FieldType', 'FieldValue', 'Group', 'Invoice', 'Item', 'Job', 'JobAssociation', 'Library', 'Membership', 'ObjectType', 'Operation', 'OperationType', 'PartAssociation', 'Plan', 'PlanAssociation', 'Sample', 'SampleType', 'Upload', 'User', 'UserBudgetAssociation', 'Wire']


For more information about these models, visit the :doc:`developer/api_reference.rst`

Models contain specific relationships to each other roughly outlined here:

.. image:: _static/Fig1_Subsystems.png
    :width: 100 %

Making queries
~~~~~~~~~~~~~~

Model queries can be made directly from the session. For example, like grab one `Sample` from
the Aquarium server:

::

    mysample = session.Sample.one()
    print(mysample)


Once loaded, model attributes can be accessed directly as class attributes:

::

    print("We just grabbed sample {} with name {}".format(mysample.id, mysample.name)



We can also grab many samples at the same time:

::

    last50 = session.Sample.last(50)   # the last 50 samples created in the database
    first25 = session.Sample.first(25)  # the first 25 samples created
    mysample2 = session.Sample.find_by_name("GFP")  # sample with name == 'GFP'
    samples = session.Sample.where({'sample_type_id


You can use where with more specific conditions

.. testcode::

    mysampletypes = session.OperationType.where({"name": "Assemble Plasmid", "deployed": True})
    print(mysampletypes[0].name)

.. testoutput::

    Assemble Plasmid

You can use where with SQL-like queries as well

.. testcode::

    mysample = session.Sample.where("id>10 AND sample_type_id<10")[0]
    print(mysample.name)

.. testoutput::

    Sample

We can also query models by querying their creation (**created_at**) or
update (**updated_at**) times:

.. testcode::

    import udatetime
    from datetime import timedelta

    last24 = udatetime.to_string(udatetime.utcnow() - timedelta(hours=24))
    jobs = session.Job.where("created_at > '{}'".format(last24))
    print("jobs found")

.. testoutput::

    jobs found

Relationship Queries
~~~~~~~~~~~~~~~~~~~~

Trident automatically makes
requests as needed for certain attributes are access from
models. For example, we know from above that `Samples` have
many `Items` associated with it and, conversely, an `Item` has
a single `Sample`. Trident allows us to access these requests
on demand. For example, the following code automatically
makes a new request for an `Item's` `Sample` using its
`.sample_id` attribute.

::

    item = session.Item.one()

    # new request equivalent to session.Sample.where({"id": item.sample_id})[0] is made here
    sample = item.sample

On the other side, we can collect all of the `Items` associated with a particular sample using:

::

    sample.items

Once these queries are made, the data is cached into the model instance. Running `sample.items` again
**will not result in a new query**, but will return the previously cached results. If you want to refresh
the query, you can set the attribute to None, which will re-initiate the appropriate query once accessed:

::

    sample.items # no query here

    sample.items = None

    sample.items # new query here


An important thing to note is that, while this make querying very convenient on the Python side of
things, it is very easy to make many unncessary requets. For information on making efficient queries
and generally how querying works, visit :doc:`querying.rst`.

Creating inventory
~~~~~~~~~~~~~~~~~~

The syntax for creating new Samples, Items, etc. is:

.. code-block:: python

    mysession.Sample.new(**kwargs).save()
    mysession.Item.new(**kwargs).save()
    mysession.Plan.new(**kwargs).save()
    # and so on

The *session.Sample.new()* syntax will instantiate the model and connect the
model to the session. Alternatively, you can create samples by manually
connecting to a session.

.. code-block:: python

    from pydent.models import Sample

    mysample = Sample(**kwargs)
    mysample.connect_to_session(session)
    mysample.save()

.. testcode::

    plasmid = session.Sample.find_by_name("puc19-pBAD-GFP")
    mysample = session.Sample.new(
        name='mysample',
        description='my optional description',
        project='my project',
        sample_type_id=session.SampleType.find_by_name("Yeast Strain").id,
        properties={
            "Mating Type": "MATa",
            "Integrant": plasmid,
            "Has this strain passed QC?": "No",
            "Integrated Marker(s)": "URA"
	    })
    mysample.save()

    print(isinstance(mysample.id, int))

.. testoutput::

    True

Setting query timeout
---------------------

The following should raise an exception if the request takes too long.

.. testcode::

    session.set_timeout(0)  # we set timeout to 0s
    try:
        session.Sample.find(100)
    except ValueError as e:
        print(e)

.. testoutput::

    Attempted to set connect timeout to 0, but the timeout cannot be set to a value less than or equal to 0.


You can increase the timeout

.. testcode::

    session.set_timeout(10)  # we set timeout to 10s
    sample = session.Sample.find(1)
    print(isinstance(sample, models.Sample))

.. testoutput::

    True


Deserializing
-------------

Nested data
~~~~~~~~~~~

Pydent automatically deserializes model relationships.
Below is an example of how pydent deserializes ``sample_type`` to a
``SampleType`` model

.. testcode::

    # nested deserialization

    s = models.Sample.load({'id': 1, 'sample_type': {'id': 3}})
    assert isinstance(s, models.Sample)
    assert isinstance(s.sample_type, models.SampleType)
    print(s.sample_type.__class__)

.. testoutput::

    <class 'pydent.models.SampleType'>


Nested models
~~~~~~~~~~~~~

.. testcode::

    mysample = models.Sample.load({
        'id': 1,
        'sample_type': models.SampleType(id=1, name="primer")
    })
    print(mysample.sample_type.name)

.. testoutput::

    primer


Relationships
~~~~~~~~~~~~~

.. testcode::

    from pydent.models import Sample, SampleType

    # create new sample
    s = Sample(name='MyPrimer', sample_type_id=1)

    # connect sample with session (will throw warning if no session is connected)
    s.connect_to_session(session)

    # find the sample type using 'sample_type_id'
    s.sample_type

    prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)

    sample_data = s.dump()
    sample_type_data = s.sample_type.dump()

    print("Sample:")
    print(prettyprint(sample_data))
    print("")
    print("SampleType:")
    print(prettyprint(sample_type_data))

.. testoutput::

    Sample:
    {
        "name": "MyPrimer",
        "project": null,
        "rid": 1,
        "sample_type_id": 1
    }

    SampleType:
    {
        "created_at": "2013-10-08T10:18:01-07:00",
        "description": "A short double stranded piece of DNA for PCR and sequencing",
        "id": 1,
        "name": "Primer",
        "rid": 1,
        "updated_at": "2015-11-29T07:55:20-08:00"
    }

Serializing
-----------

.. testcode::


    sample_type = session.SampleType.find(1)
    prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)

    print(prettyprint(sample_type.dump()))

.. testoutput::

    {
        "created_at": "2013-10-08T10:18:01-07:00",
        "description": "A short double stranded piece of DNA for PCR and sequencing",
        "id": 1,
        "name": "Primer",
        "rid": 1,
        "updated_at": "2015-11-29T07:55:20-08:00"
    }

*only* fields
~~~~~~~~~~~~~

.. testcode::

    prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)
    s = session.SampleType.find(1)
    sdata = s.dump(only=('name', 'description'))

    print(prettyprint(sdata))

.. testoutput::

    {
        "description": "A short double stranded piece of DNA for PCR and sequencing",
        "name": "Primer",
        "rid": 1
    }

only some relationships
~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    s = session.SampleType.find(1)
    sdata = s.dump(relations=('items',))

    print(prettyprint(sdata))

.. testoutput::

    {
        "created_at": "2013-10-08T10:18:01-07:00",
        "description": "A short double stranded piece of DNA for PCR and sequencing",
        "id": 1,
        "name": "Primer",
        "rid": 1,
        "updated_at": "2015-11-29T07:55:20-08:00"
    }

all relationships
~~~~~~~~~~~~~~~~~

.. code::

    s = session.SampleType.find(1)
    print(prettyprint(s.dump(all_relations=True)))
    """
    {'created_at': '2013-10-08T10:18:48-07:00',
    'data': None,
    'description': None,
    'field_values': [{'allowable_field_type_id': None,
                           'child_item_id': None,
                           'child_sample_id': None,
                           'column': None,
                           'created_at': '2016-05-09T20:41:06-07:00',
                           'field_type_id': None,
                           'id': 67853,
                            ...
    ...
    }
    """

.. testcode::
    :hide:

    s = session.SampleType.find(1)
    prettyprint(s.dump(all_relations=True))
    print('ok')

.. testoutput::
    :hide:

    ok

complex serialization
~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    s = session.Sample.find(1)
    sdata = s.dump(
        include={
            'items': {                  # serialize the items
                'object_type': {        # serialize the object_type for each item
                    'opts': {
                        'only': 'name'  # only serialize the name for the object_type
                    }
                },
            'opts': {
                'only': 'id'            # only serialize the id for each item (in addition to the object_type)
                }
            }
    })

    print(prettyprint(sdata))


.. testoutput::

    {
        "created_at": "2013-10-08T10:18:48-07:00",
        "data": null,
        "description": null,
        "id": 1,
        "items": [
            {
                "id": 438,
                "object_type": {
                    "name": "Primer Aliquot",
                    "rid": 1
                },
                "rid": 1
            },
            {
                "id": 441,
                "object_type": {
                    "name": "Plasmid Stock",
                    "rid": 1
                },
                "rid": 1
            }
        ],
        "name": "IAA1-Nat-F",
        "project": "Auxin",
        "rid": 1,
        "sample_type_id": 1,
        "updated_at": "2013-10-08T10:18:48-07:00",
        "user_id": 1
    }

Planning
--------

Submitting a Plan
~~~~~~~~~~~~~~~~~

.. testcode::

    primer = session.SampleType.find(1).samples[-1]

    # get Order Primer operation type
    ot = session.OperationType.find(328)

    # create an operation
    order_primer = ot.instance()

    # set io
    order_primer.set_output("Primer", sample=primer)
    order_primer.set_input("Urgent?", value="no")

    # create a new plan
    p = models.Plan(name="MyPlan")

    # connect the plan to the session
    p.connect_to_session(session)

    # add the operation to the plan
    p.add_operation(order_primer)

    # save the plan
    p.create()

    # estimate the cost
    p.estimate_cost()

    # validate the plan
    p.validate()

    # show the plan
    # p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("Your plan was submitted successfully!")
    print(p.id is not None)

.. testoutput::

    Your plan was submitted successfully!
    True


Submitting a Gibson Assembly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    # find "Assembly Plasmid" protocol
    gibson_type = session.OperationType.where({"deployed": True, "name": "Assemble Plasmid"})[0]

    # instantiate gibson operation
    gibson_op = gibson_type.instance()
    gibson_op.field_values = []


    # set output
    gibson_op.set_output("Assembled Plasmid", sample=session.Sample.find_by_name("pCAG-NLS-HA-Bxb1"))

    # set input 1
    gibson_op.add_to_input_array("Fragment",
                                 sample=session.Sample.find_by_name("SV40NLS1-FLP-SV40NLS2"),
                                 item=session.Item.find(84034))

    # set input 2
    gibson_op.add_to_input_array("Fragment",
                                 sample=session.Sample.find_by_name("CRPos0-HDAC4_split"),
                                 item=session.Item.find(83714))


    # set input 3
    sample = session.Sample.find_by_name("_HDAC4_split_part1")
    fv = gibson_op.add_to_input_array("Fragment",
                                 sample=sample)

    # PCR
    pcr_type = session.OperationType.where({"deployed": True, "name": "Make PCR Fragment"})[0]
    pcr_op = pcr_type.instance()
    pcr_op.set_input("Forward Primer", sample=sample.field_value("Forward Primer").sample)
    pcr_op.set_input("Reverse Primer", sample=sample.field_value("Forward Primer").sample)
    pcr_op.set_input("Template", sample=sample.field_value("Template").sample)
    pcr_op.set_output("Fragment", sample=sample)

    # Run gel
    gel_type = session.OperationType.where({"deployed": True, "name": "Run Gel"})[0]
    gel_op = gel_type.instance()
    gel_op.set_input("Fragment", sample=sample)
    gel_op.set_output("Fragment", sample=sample)

    # extract gel
    extract_type = session.OperationType.where({"deployed": True, "name": "Extract Gel Slice"})[0]
    extract_op = extract_type.instance()
    extract_op.set_input("Fragment", sample=sample)
    extract_op.set_output("Fragment", sample=sample)

    # purify gel slice
    purify_type = session.OperationType.where({"deployed": True, "name": "Purify Gel Slice"})[0]
    purify_op = purify_type.instance()
    purify_op.set_input("Gel", sample=sample)
    purify_op.set_output("Fragment", sample=sample)

    # create a new plan and add operations
    p = models.Plan(name="MyPlan")
    p.connect_to_session(session)
    p.add_operation(gibson_op)
    p.add_operation(pcr_op)
    p.add_operation(gel_op)
    p.add_operation(extract_op)
    p.add_operation(purify_op)

    # wires
    p.wire(purify_op.output("Fragment"), fv)
    p.wire(extract_op.output("Fragment"), purify_op.input("Gel"))
    p.wire(gel_op.output("Fragment"), extract_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))

    # save the plan
    p.create()

    # estimate the cost
    p.estimate_cost()

    # validate the plan
    p.validate()

    # show the plan
    # p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("Your plan was submitted successfully!")
    print(p.id is not None)

.. testoutput::

    Your plan was submitted successfully!
    True
