from pydent import AqSession, pprint
from pydent.models import *


nursery = AqSession("vrana", "Mountain5", "http://52.27.43.242:81/")

plan = nursery.Plan.find_using_session(53544)
fv = plan.operations[0].field_values[0]
ft = fv.field_type
pprint(ft.dump(dump_all_relations=True))
# pprint(fv.dump(dump_all_relations=True, dump_depth=2))