Trident Examples
================

Basic Usage
-----------

Logging in
~~~~~~~~~~

.. code:: python

    from pydent import AqSession

    nursery = AqSession("username", "password", "url")
    production = AqSession("username", "password", "url2")

And, to login interactively

.. code:: python

    nursery = AqSession.interactive()
    # enters interactive shell

Model queries
~~~~~~~~~~~~~

.. code:: python

    session # your AqSession

    # find Sample with id=1
    session.Sample.find(1)

    # find SampleTypes with name="Primer"
    session.SampleType.find_by_name("Primer")

    # find all SampleTypes
    session.SampleType.all()

    # find Operations where name="Transfer to 96 Well Plate"
    session.Operations.where({'name': 'Transfer to 96 Well Plate'})

    # list all available models
    session.models

Setting a query timeout
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    # raises timeout exception if request takes too long
    try:
        session.FieldValue.all()
    except Exception:
        print("Request took too long!")

    session.set_timeout(60)
    session.FieldValue.all()
    print("Great!")

Deserializing
-------------

Deserializing nested data
~~~~~~~~~~~~~~~~~~~~~~~~~

pydent knows to automatically deserialize ``sample_type`` to a
``SampleType`` model

.. code:: python

    from pydent.models import Sample, SampleType

    # nested deserialization

    s = Sample.load({'id': 1, 'sample_type': {'id': 3}})
    assert isinstance(s, Sample)
    assert isinstance(s.sample_type, SampleType)

Deserializing with nested models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    Sample.load({
        'id': 1
        'sample_type': SampleType(id=1, name="primer")
    }

Find relationships using requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from pydent.models import Sample, SampleType
    from pydent import AqSession

    nursery = AqSession("username", "password", "url")

    # create new sample
    s = Sample(name='MyPrimer', sample_type_id=1)

    # connect sample with session (will throw warning if no session is connected)
    s.connect_to_session(nursery)

    # find the sample type using 'sample_type_id'
    s.sample_type

    assert isinstance(s.sample_type, SampleType)
    print(s.sample_type)

    """
    <class 'pydent.models.SampleType'>: {
        "id": 1,
        "created_at": "2013-10-08T10:18:01-07:00",
        "name": "Primer",
        "description": "A short double stranded piece of DNA for PCR and sequencing",
        "updated_at": "2015-11-29T07:55:20-08:00",
    "samples": "<HasMany (model=Sample, callback=where_using_session, params=(<function HasMany.__init__.<locals>.<lambda> at 0x10c3b7620>,))>",
        "field_types": "<Many (model=FieldType, callback=where_using_session, params=(<function SampleType.<lambda> at 0x10c3b76a8>,))>"
    }
    """

Serializing
-----------

.. code:: python

    s = session.SampleType.find(1)
    s.dump()

    """
    {'created_at': '2013-10-08T10:18:01-07:00',
     'description': 'A short double stranded piece of DNA for PCR and sequencing',
     'id': 1,
     'name': 'Primer',
     'updated_at': '2015-11-29T07:55:20-08:00'}
    """

Serialize with *only* some fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    s.dump(only=('data', 'name', 'description'))
    # {'name': 'IAA1-Nat-F', 'description': None, 'data': None}

Serialize with some relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from pydent import pprint

    pprint(s.dump(relations=('items',)))

Serialize with all relationships
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from pydent import pprint

    pprint(s.dump(all_relations=True))
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

complex serialization
~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    # deserialize operations and wires. For wires, also include source and destination
    # field_values. For operation.field_values, include allowable_field_type and operation_type.
    # for operation_type, only serialize name

    json_data = plan.dump(include={
        'operations': {
           'field_values': 'allowable_field_type',
           'operation_type': {'opts': {'only': ['name']}},
        },
        'wires': {"source", "destination"}
    })

Planning
--------

Submitting a Plan
~~~~~~~~~~~~~~~~~

.. code:: python

    session = AqSession.interactive()

    primer = session.SampleType.find(1).samples[-1]

    # get Order Primer operation type
    ot = session.OperationType.find(328)

    # create an operation
    order_primer = ot.instance()

    # set io
    order_primer.set_output("Primer", sample=primer)
    order_primer.set_input("Urgent?", value="no")

    # create a new plan and add operations
    p = session.Plan(name="MyPlan")
    p.add_operation(order_primer)

    # save the plan
    p.create()

    # estimate the cost
    p.estimate_cost()

    # validate the plan
    p.validate()

    # show the plan
    p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("You may open you plan here: {}".format(session.url + "/plans?plan_id={}".format(p.id)))


Submitting a Gibson Assembly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

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
    p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("You may open you plan here: {}".format(session.url + "/plans?plan_id={}".format(p.id)))

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
