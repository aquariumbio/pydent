from pydent.planner import Planner
from os.path import dirname, abspath, join
import dill


def test_pickle_multiplan(session):

    p = session.Plan.find(33672)
    canvas = Planner(p)

    here = dirname(abspath(__file__))
    with open(join(here, 'multiplan.pkl'), 'wb') as f:
        dill.dump(canvas, f)