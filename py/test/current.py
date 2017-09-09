import sys
sys.path.append('.')

import aq

aq.login()

print("The current user is " + aq.User.current.name)
