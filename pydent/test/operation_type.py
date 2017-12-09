import aq

aq.login()

ot = aq.OperationType.find_by_name("Make PCR Fragment")

print(ot.name)

for ft in ot.field_types:
    print("  - " + ft.role + ": " + ft.name + "(" + ft.ftype + ")")
    if ft.ftype == "sample":
        for aft in ft.allowable_field_types:
            st_name = aft.sample_type.name if aft.sample_type else "no sample type"
            ot_name = aft.object_type.name if aft.object_type else "no object type"
            print("    - " + st_name + " / " + ot_name)

print([op.id for op in ot.operations])
