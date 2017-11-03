from pydent import *

Session.create_from_config_file("secrets/config.json")

fvs = aq.FieldValue.where("name = 'Overhang Sequence' and value regexp '^aaaaa'")

print([fv.value for fv in fvs])
