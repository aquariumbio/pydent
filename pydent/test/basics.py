from pydent import *

Session.create_from_config_file("secrets/config.json")

u = aq.User.find(1)
print("User " + str(u.id) + " is named " + u.name)

i = aq.Item.find(1111)
print("Item " + str(i.id) +
      " is a " + i.sample.sample_type.name +
      " named " + i.sample.name +
      " created at " + i.created_at)

sts = aq.SampleType.all()
print("All Sample Types:")
[ print("    " + st.name) for st in sts ]

s = aq.Sample.find_by_name("pGFP")
print("Sample named " + s.name + " has id " + str(s.id))

samples = aq.Sample.where({"id": [1231,2341,3451]})
[ print("Sample " + str(sample.id) +
        " is a " + sample.sample_type.name +
        " named " + sample.name)
  for sample in samples ]
