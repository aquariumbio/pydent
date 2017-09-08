import sys
sys.path.append('.')

import aq

aq.login()

# You can get has_many associations

s = aq.Sample.find_by_name("pGFP")
print([i.location for i in s.items])

# If you include the association, then Trident knows to convert the
# data it gets to a list of the right record type, and not do another
# query.

s = aq.Sample.where({"name": "pGFP"}, { "include": "items"}, {})
print([i.location for i in s[0].items])
