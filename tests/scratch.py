from pydent import AqSession, pprint
from pydent.models import *
from pydent.aqhttp import AqHTTP

nursery = AqSession("vrana", "Mountain5", "http://52.27.43.242:81/")

ot = nursery.OperationType.all()[-1]

# print(ot.operation_type)

print(ot.protocol)

print(ot.documentation)

print(ot.precondition)

print(ot.cost_model)

lib = nursery.Library.all()[-1]

print(lib.source)