Trident Examples
================

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


Basic Usage
-----------

Logging in
~~~~~~~~~~

.. code:: python

    from pydent import AqSession, models

    nursery = AqSession("username", "password", "url")
    production = AqSession("username", "password", "url2")

And, to login interactively

.. code:: python

    nursery = AqSession.interactive()
    # enters interactive shell

Model queries
~~~~~~~~~~~~~

Find Sample with id==1


.. testcode::

    mysample = session.Sample.find(1)
    print(mysample.id)

.. testoutput::

    1

Find SampleTypes with name=="Primer"


.. testcode::

    mysample = session.SampleType.find_by_name("Primer")
    print(mysample.name)

.. testoutput::

    Primer


Find OperationType where name="Transfer to 96 Well Plate". The method
will return an array where the conditions are true.

.. testcode::

    myoperation = session.OperationType.where({"name": "Order Primer"})[0]
    print(myoperation.name)

.. testoutput::

    Order Primer


You can use where with more specific conditions

.. testcode::

    mysampletypes = session.OperationType.where({"name": "Assemble Plasmid", "deployed": True})
    print(mysampletypes[0].name)

.. testoutput::

    Assemble Plasmid

You can use where with SQL-like queries as well

.. testcode::

    mysample = session.SampleType.where("id=1")[0]
    print(mysample.name)

.. testoutput::

    Primer

Here's an example of finding all Jobs created in the last 24 hours

.. testcode::

    import udatetime
    from datetime import timedelta

    last24 = udatetime.to_string(udatetime.utcnow() - timedelta(hours=24))
    jobs = session.Job.where("created_at > '{}'".format(last24))
    print("jobs found")

.. testoutput::

    jobs found

Use session.models to list all available models in Aquarium.

.. testcode::

    print(session.models)

.. testoutput::

    ['Account', 'AllowableFieldType', 'Budget', 'Code', 'Collection', 'DataAssociation', 'FieldType', 'FieldValue', 'Group', 'Invoice', 'Item', 'Job', 'JobAssociation', 'Library', 'Membership', 'ObjectType', 'Operation', 'OperationType', 'Plan', 'PlanAssociation', 'Sample', 'SampleType', 'Upload', 'User', 'UserBudgetAssociation', 'Wire']


Creating Samples
~~~~~~~~~~~~~~~~

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

Setting a query timeout
~~~~~~~~~~~~~~~~~~~~~~~

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
    session.Sample.find(1)
    print("Great!")

.. testoutput::

    Great!


Deserializing
-------------

Deserializing nested data
~~~~~~~~~~~~~~~~~~~~~~~~~

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


Deserializing with nested models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

    mysample = models.Sample.load({
        'id': 1,
        'sample_type': models.SampleType(id=1, name="primer")
    })
    print(mysample.sample_type.name)

.. testoutput::

    primer


Find relationships using requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Serialize with *only* some fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Serialize with some relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Serialize with all relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Miscellaneous
-------------

Magic chaining
~~~~~~~~~~~~~~

You can chain together attributes and function calls:

.. code-block:: python

    # using tradiational list comprehension
    [s.name for s in session.SampleType.find(1).samples][:10]

    # or using magicchain
    pprint(session.SampleType.find(1).samples.name[:10])

    # returns
    # ['IAA1-Nat-F', 'prKL1573', 'prKL744', 'prKL1927', 'prKL1928',
    # 'prKL1929', 'prKL1930', 'prKL506', 'prKL1708', 'lacI\_h2']


.. code:: python


    pcr = session.OperationType.find_by_name("Make PCR Fragment")

    pprint(pcr.operations[0:5].field_values.name
    [['Forward Primer', 'Reverse Primer', 'Template', 'Fragment'],
     ['Forward Primer', 'Reverse Primer', 'Template', 'Fragment'],
     ['Forward Primer', 'Reverse Primer', 'Template', 'Fragment'],
     ['Forward Primer', 'Reverse Primer', 'Template', 'Fragment'],
     ['Forward Primer', 'Reverse Primer', 'Template', 'Fragment']]

    pprint(pcr.operations[0:5].field_values.item.id)
    [[114549, 62943, 22929, 114553],
     [114564, 62943, 22929, 114566],
     [114737, 62943, 22929, 114739],
     [114748, 62943, 22929, 114750],
     [114782, 62943, 22929, 114784]]
