import json
import sys
import os
from subprocess import call

import aq

aq.login()

id = int(sys.argv[1])
directory = "plan_" + sys.argv[1]
plan = aq.Plan.find(id)

if not os.path.exists(directory):
    os.makedirs(directory)

serialized_plan = json.dumps(plan.to_json(include=[
    "wires",
    "data_associations",
    { "operations": [
        "operation_type",
        { "field_values": [
                "field_type",
                "allowable_field_type",
                { "sample": [ "sample_type" ] },
                { "item": [ "object_type", "data_associations" ] }
            ]
        },
        "data_associations",
        "jobs"
    ]}
]), indent=4, sort_keys=True)

file = open(directory + "/plan.json" , 'w+')
file.write(serialized_plan)
file.close

for da in plan.all_data_associations():
    if da.upload:
        file = open(directory + "/upload_" + str(da.upload.id) + "_" + da.upload.upload_file_name, 'bw+')
        file.write(da.upload.data)
        file.close

call(["tar", "czvf", directory + "tar.gz", directory])
