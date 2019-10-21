from os.path import abspath
from os.path import dirname
from os.path import join

import dill

from pydent.planner import Planner


def test_pickle_multiplan(session):

    p = session.Plan.find(33672)
    canvas = Planner(p)

    here = dirname(abspath(__file__))
    with open(join(here, "multiplan.pkl"), "wb") as f:
        dill.dump(canvas, f)
