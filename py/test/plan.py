import aq

aq.login()

plan = aq.Plan.find(976)
print("Plan " + str(plan.id) + ": " + plan.name)

for op in plan.operations:
    print("  - " + str(op.id) +
          ": " + op.operation_type.name +
          "(" + op.status + ")" +
          "jobs: " + str([j.id for j in op.jobs]))
    for fv in op.field_values:
        item_id = fv.item.id if fv.item else "none"
        print("    - " + fv.role + ": " + fv.name + " => " + str(item_id))

for wire in plan.wires:
    print(wire.source.operation.operation_type.name +
          ":" + wire.source.name +
          " => " + wire.destination.operation.operation_type.name +
          ":" + wire.destination.name)

# Note that wires are not currently available for plans not
# retrieved via 'find', because there is no easy server side
# method to do that.
print(aq.Plan.where({"id": 976})[0].wires)
