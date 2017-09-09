import sys
sys.path.append('.')

import aq

aq.login()

st = aq.SampleType.find_by_name("Plasmid")

print("Sample Type " + str(st.id) + ": " + st.name)

for ft in st.field_types:
    print("  - " + ft.name + ": " + ft.ftype)
    if ft.ftype == "sample":
        for aft in ft.allowable_field_types:
            st_name = aft.sample_type.name if aft.sample_type else "no sample type"
            print("    - " + st_name)
