from pydent import AqSession


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
p._add_operation(order_primer)

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