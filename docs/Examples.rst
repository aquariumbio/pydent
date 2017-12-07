Trident Examples
================

Basic
-----

**logging in**

.. code:: python

    from pydent import AqSession

    nursery = AqSession("username", "password", "url")
    production = AqSession("username", "password", "url2")

**interactive login**

.. code:: python

    nursery = AqSession.interactive()
    # enters interactive shell

**getting models**

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

**set timout**

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

**deserializing nested data**

pydent knows to automatically deserialize 'sample\_type' to a
'SampleType' model from pydent.models import Sample, SampleType

.. code:: python

    # nested deserialization

    s = Sample.load({'id': 1, 'sample_type': {'id': 3}})
    assert isinstance(s, Sample)
    assert isinstance(s.sample_type, SampleType)

**deserializing with nested models**

.. code:: python

    Sample.load({
        'id': 1
        'sample_type': SampleType(id=1, name="primer")
    }

**find relationships using requests**

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

**serialize with *only* some fields**

.. code:: python

    s.dump(only=('data', 'name', 'description'))
    # {'name': 'IAA1-Nat-F', 'description': None, 'data': None}

**serialize with some relations**

.. code:: python

    from pydent import pprint

    pprint(s.dump(relations=('items',)))

**serialize with all relations**

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

**complex serializing**

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

Misc
----

**magic chaining** you can chain together attributes and function calls
\`\`\`python [s.name for s in session.SampleType.find(1).samples][:10]
pprint(session.SampleType.find(1).samples.name[:10])

['IAA1-Nat-F', 'prKL1573', 'prKL744', 'prKL1927', 'prKL1928',
'prKL1929', 'prKL1930', 'prKL506', 'prKL1708', 'lacI\_h2'] \`\`\`

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
