def test_code_callback(session):

    ot = session.OperationType.one()
    protocol = ot.protocol
    print(protocol)
