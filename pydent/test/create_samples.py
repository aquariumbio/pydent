import time
from pydent import *

Session.create_from_config_file("secrets/config.json")

n = int(time.time())%1000 # chosen so you get a different name each time

# Make a simple sample with no nested samples
p = aq.Sample.record({

    # basic fields here
    "sample_type_id": aq.SampleType.find_by_name("Primer").id,
    "name": "my new trident primer " + str(n),
    "description": "A new primer made from within Trident",
    "project": "trident",

    # fields defined in sample type definition here
    "field_values": [
        { "name": "Overhang Sequence", "value": "actggactagc" },
        { "name": "Anneal Sequence", "value": "cccgggcc" },
        { "name": "T Anneal", "value": 60 }]
})

# Make a complex sample that referes to two existing samples, and creates a
# new sub-sample.
f = aq.Sample.record({

    # basic fields here
    "sample_type_id": aq.SampleType.find_by_name("Fragment").id,
    "name": "my new trident fragment " + str(n),
    "description": "mad from within Trident!",
    "project": "trident",

    # fields defined in sample type definition here
    "field_values": [

        # a basic field
        { "name": "Length", "value": 2017 },

        # a field that references to a child sanme by its "identifier"
        { "name": "Forward Primer",
          "child_sample_name": aq.Sample.find(20297).identifier },

        # a field that describes its required sub-sample completely
        { "name": "Reverse Primer", "new_child_sample": aq.Sample.record({
            "sample_type_id": aq.SampleType.find_by_name("Primer").id,
            "name": "my nested trident primer " + str(n),
            "description": "A new primer made from within Trident",
            "project": "trident",
            "field_values": [
                { "name": "Overhang Sequence", "value": "tactcgacgactagctagct" },
                { "name": "Anneal Sequence", "value": "acagtcagctagctagca" },
                { "name": "T Anneal", "value": 71 }]})},

        # another field that refers to an existing sample
        { "name": "Template",
          "child_sample_name": aq.Sample.find_by_name("pGFP").identifier }

    ]
})

# Make both samples
slist = aq.Sample.create([p,f])

print(slist)
