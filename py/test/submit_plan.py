import sys
sys.path.append('.')

import aq

print("Choose a budget")
aq.login()
budgets = aq.User.current.budgets
if len(budgets) > 0:
    budget = budgets[0]
    print("Using budget " + budget.name)
else:
    print("No budgets available. Quitting.")
    exit(1)

# Get a sample
print("Setting up sample")
primer = aq.Sample.find_by_name("test1")
ly_primer = aq.ObjectType.find_by_name("Lyophilized Primer")
primer_aliquot = aq.ObjectType.find_by_name("Primer Aliquot")
primer_stock = aq.ObjectType.find_by_name("Primer Stock")

# Make some operations
print("Make operations assign i/o")
order_primer = aq.OperationType.find_by_name("Order Primer").instance()
rehydrate_primer = aq.OperationType.find_by_name("Rehydrate Primer").instance()

# Set the I/O of the operations
rehydrate_primer.set_input("Primer", sample=primer, container=ly_primer) \
                .set_output("Primer Aliquot", sample=primer, container=primer_aliquot) \
                .set_output("Primer Stock", sample=primer, container=primer_stock)

order_primer.set_output("Primer", sample=primer) \
            .set_input("Urgent?", value="No")

# Make a plan
print("Make a plan")
plan = aq.Plan.record({"name": "My new plan"})
plan.add_operation(order_primer) \
    .add_operation(rehydrate_primer) \
    .wire(order_primer.output("Primer"),rehydrate_primer.input("Primer"))

print("Validate the plan")
# Validate the plan
if not aq.algorithms.validate.plan(plan):
    print("The plan is not valid. Please address the errors and try again.")
    for msg in aq.algorithms.validate.messages():
        print("  " + msg)
    exit(1)

print("Save the plan and determine costs")
# Save plan and estimate costs
plan.save()
plan.estimate_cost()

print("Show the plan")
# Print out the plan to see if it looks legit
plan.show()

print("Submit the plan")
plan.submit(aq.User.current,budget)
