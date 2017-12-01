from pydent import AqSession, pprint
from pydent.models import *
from pydent.aqhttp import AqHTTP

nursery = AqSession("vrana", "Mountain5", "http://52.27.43.242:81/")

# d = nursery.get('operation_types/1077/stats')

ft = nursery.FieldType.find(9070)

ft.print(all_relations=True)