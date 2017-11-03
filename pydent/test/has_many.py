from pydent import *

AqSession.create_from_config_file("secrets/config.json")

# You can get has_many associations

s = aq.Sample.find_by_name("pGFP")
print([i.location for i in s.items])

# If you include the association, then Trident knows to convert the
# data it gets to a list of the right record type, and not do another
# query.

s = aq.Sample.where({"name": "pGFP"}, {"include": "items"}, {})
print([i.location for i in s[0].items])

# Tests

print("")
print([s.name for s in aq.User.find(1).samples])

print("")
print([s.name for s in aq.SampleType.find_by_name("Enzyme").samples])
