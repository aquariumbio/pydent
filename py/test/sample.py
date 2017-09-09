import sys
sys.path.append('.')

import aq

aq.login()

s = aq.Sample.find(20219)
print("\nSample " + str(s.id) + ": " + s.name)

print("\n  Description")
for fv in s.field_values:
    if fv.sample:
        print("    - " + fv.name + ": " + str(fv.sample.name))
    else:
        print("    - " + fv.name + ": " + str(fv.value))


print("\n Inventory")
for item in s.items:
    print("    - " + str(item.id) + ": " + item.location)

print("")
