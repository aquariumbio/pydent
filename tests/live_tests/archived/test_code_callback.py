def test_code_callback_operation_type(session):

    ot = session.OperationType.one()
    for accessor in ['protocol', 'precondition', 'documentation', 'cost_model']:
        code = getattr(ot, accessor)
        assert code
        assert code.parent_id == ot.id
        assert code.name == accessor
        assert code.parent_class == "OperationType"


def test_code_callback_library(session):

    ot = session.Library.one()
    for accessor in ['source']:
        code = getattr(ot, accessor)
        assert code
        assert code.parent_id == ot.id
        assert code.name == accessor
        assert code.parent_class == "Library"


