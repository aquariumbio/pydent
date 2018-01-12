from pydent.models import Operation
from pydent import pprint
import json

def test_main(session):

    def test_operation_type(op, num_ops, use_precondition=False):
        # create random operatoins
        test_ops_data = session.utils.aqhttp.get(f'operation_types/{op.id}/random/{num_ops}')

        # create data for POST
        data = op.dump()
        data['test_operations'] = test_ops_data
        data['use_precondition'] = True
        pprint(data)

        # run tests
        result = session.utils.aqhttp.post('operation_types/test', json_data=data)

        # display the result
        print("\n\nRESULT")
        # pprint(result)

        state = result['job']['state']

        state = json.loads(state)
        pprint(state)

    # if operation passes, last step should have 'operation': 'complete' in it and no 'backtrace'

    op = session.OperationType.find(382)
    test_operation_type(op, 5)
