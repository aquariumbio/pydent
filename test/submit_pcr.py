# import sys
# sys.path.append('.') # Todo: Figure out how to add python search path to the shell
# sys.path.append('./cloning')
#
from pydent.cloning import pcr
from pydent import *

AqSession.create_from_config_file("secrets/config.json")

pcr = pcr.Plan("My PCR Plan")
fragment = aq.Sample.find_by_name("optimization-test-fragment")
fragment_stock = aq.ObjectType.find_by_name("Fragment Stock")

pcr.set_output(fragment, fragment_stock)
pcr.show()

if not algorithms.validate.plan(pcr):
    print("The plan is not valid. Please address the errors and try again.")
    for msg in algorithms.validate.messages():
        print("  " + msg)
    exit(1)

pcr.save()
budget = User.current.budgets[0]
pcr.submit(User.current, budget)
