import sys
sys.path.append('.')

import aq

aq.login()

fvs = aq.FieldValue.where("name = 'Overhang Sequence' and value regexp '^aaaaa'")

print([fv.value for fv in fvs])
