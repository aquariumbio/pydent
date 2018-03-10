.. Trident documentation master file, created by
   sphinx-quickstart on Sun Nov 19 22:18:51 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Trident: The Aquarium API
=========================

Trident is the Python scripting API for Aquarium, the software that runs the 
`UW BIOFAB <http://www.uwbiofab.org>`_.
The `code respository <https://github.com/klavinslab/trident>`_ is available to members of the 
`Klavins lab <https://github.com/klavinslab/>`_ GitHub
organization, which consists of lab members and collaborators.
There is also a Javascript version of Trident available to that group.

.. toctree::
   :hidden:

   self

Trident is a python scripting API wrapper for Aquarium. With Trident,
you may pull down data, submit plans, create samples, and more.

**Installation**

To get started, checkout the :doc:`user/installation`

**Using Trident**

Below is an example of how to submit a plan. Check :doc:`user/examples` for more examples.

.. code:: python

    from pydent import AqSession, models

    session = AqSession.interactive()

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
    p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("You may open you plan here: {}".format(session.url + "/plans?plan_id={}".format(p.id)))


**Contributing**

To contribute, please checkout :doc:`developer/contributing`.


Read More
-----------------

Check out the table of contents below (and to the left).

.. toctree::
   :maxdepth: 2

   user/installation
   user/examples
   developer/api_reference
   developer/api_notes
   developer/contributing
   developer/tests



