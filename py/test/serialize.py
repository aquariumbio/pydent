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
