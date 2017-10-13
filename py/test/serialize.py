import json
import aq

aq.login()

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
def my_to_json(self,include=[],exclude=[]):
    return { "i": len(include), "e": len(exclude) }

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
