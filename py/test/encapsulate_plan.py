import sys
sys.path.append('.')

import aq
import pcr

aq.login()

pcr = pcr.Plan("My PCR Plan");
fragment = aq.Sample.find_by_name("optimization-test-fragment")
fragment_stock = aq.ObjectType.find_by_name("Fragment Stock")

pcr.set_output(fragment,fragment_stock)
pcr.show()

if not aq.algorithms.validate.plan(pcr):
    print("The plan is not valid. Please address the errors and try again.")
    for msg in aq.algorithms.validate.messages():
        print("  " + msg)
    exit(1)

pcr.save()

budget = aq.User.current.budgets[0]
pcr.submit(aq.User.current, budget)
