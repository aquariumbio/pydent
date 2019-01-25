.. Trident documentation master file, created by
   sphinx-quickstart on Sun Nov 19 22:18:51 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Trident: The Aquarium API
=========================

Trident is the Python scripting API for
`Aquarium <https://www.aquarium.bio/>`_
, the software that runs the 
`UW BIOFAB <http://www.uwbiofab.org>`_.
The code is available `here <https://github.com/klavinslab/trident>`_ 
and was built by members of the 
`Klavins lab <http://klavinslab.org/>`_.

.. toctree::
   :hidden:

   self

Trident is a python scripting API wrapper for Aquarium. With Trident,
you may pull down data, submit plans, create samples, and more.

**Getting Started**

Pydent can be install using pip:

::

   pip3 install pydent --upgrade

To use trident, you'll need an Aquarium login, password, and url

::

   python

::

   from pydent import AqSession

   session = AqSession("user", "password", "http://you.aquarium.url")

   sample = session.Sample.find(1)

   print(sample)

**More Installation Instructions**

For more information on installation, checkout the :doc:`user/installation`

**Using Trident**

Below is an example of how to submit a plan. Check :doc:`user/examples` for more examples.


.. testsetup::

    import os
    import json
    from pydent import AqSession, models

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

    prettyprint = lambda x: json.dumps(x, indent=4, sort_keys=True)

    session = session()


.. testcode::

    # session = AqSession("user", "password", "http://you.aquarium.url")

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

    # create the plan on the server
    p.create()

    # changes to plan can be saved (not necessary here)
    # p.save()

    # estimate the cost
    p.estimate_cost()

    # validate the plan
    p.validate()

    # show the plan
    # p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    # print("You may open you plan here: {}".format(session.url + "/plans?plan_id={}".format(p.id)))
    print("Your plan was successfully submitted!")

.. testoutput::

   Your plan was successfully submitted!


**Contributing**

To contribute, please checkout :doc:`developer/contributing`.


Read More
-----------------

Check out the table of contents below (and to the left).

.. toctree::
   :maxdepth: 2

   user/installation
   user/planning
   user/examples
   developer/api_reference
   developer/api_notes
   developer/contributing
   developer/tests



