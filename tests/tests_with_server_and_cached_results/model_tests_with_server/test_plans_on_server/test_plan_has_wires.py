def test_plan_has_wires(session):
    session._aqhttp.log.set_level("DEBUG")
    plan = session.Plan.one()
    print(plan.raw)
