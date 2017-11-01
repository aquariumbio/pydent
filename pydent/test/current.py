from pydent import *

AqSession.create_from_config_file("secrets/config.json")

print("The current user is " + aq.User.current.name)
