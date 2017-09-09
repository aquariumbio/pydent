import sys
sys.path.append('.')

import aq

aq.login()

plan = aq.Plan.find(976)
print("Plan " + str(plan.id) + ": " + plan.name)

for op in plan.operations:
    print("  - " + str(op.id) + ": " + op.operation_type.name + "(" + op.status + ")")
    for fv in op.field_values:
        item_id = fv.item.id if fv.item else "none"
        print("    - " + fv.role + ": " + fv.name + " => " + str(item_id))
