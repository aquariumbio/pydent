from pydent import AqSession
from pydent.models import *


nursery = AqSession.interactive()

# ===== MANUAL CREATION =====
# you can create models from scratch...
sample = Sample()

# but they won't have a session attached
try:
    sample.sample_type
except:
    print("opps, no session attached")

# you can manually connect to a session
sample.connect_to_session(nursery)

# ===== SESSION CREATION =====
# or you can create models from the session
sample = nursery.Sample()

# you can pre-load attributes to the models
sample = nursery.Sample(name="MyNewSample", description="SomeDescription")

# and then you can serialize
sample.dump()