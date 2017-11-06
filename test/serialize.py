import json
import time
from pydent import *

AqSession.create_from_config_file("secrets/config.json")

p = aq.SampleType.find_by_name("Plasmid")

print(json.dumps(p.to_json(include=[
    {
        "field_types": [
            {
                "allowable_field_types": [
                    "object_type",
                    "sample_type"
                ]
            }
        ]
    }
])))

# temporarily override the to_json method of field types


def my_to_json(self, include=[], exclude=[]):
    j = super(aq.FieldTypeRecord, self).to_json(
        include=include, exclude=exclude)
    j["timestamp"] = time.time()
    return j


aq.FieldTypeRecord.to_json = my_to_json

print(json.dumps(p.to_json(include=[
    {
        "field_types": [
            {
                "allowable_field_types": [
                    "object_type",
                    "sample_type"
                ]
            }
        ]
    }
])))
