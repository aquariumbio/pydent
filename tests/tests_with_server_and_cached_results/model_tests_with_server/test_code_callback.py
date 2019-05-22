from pydent.models import Code


def test_code_callback_operation_type(session):
    """OperationTypes should have protocol, precondition, docuemntation, and cost_model codes"""
    ot = session.OperationType.one()
    for accessor in ['protocol', 'precondition', 'documentation', 'cost_model']:
        code = getattr(ot, accessor)
        assert isinstance(code, Code)
        assert code.parent_id == ot.id
        assert code.name == accessor
        assert code.parent_class == "OperationType"


def test_code_callback_library(session):
    """Library should have only a source code"""
    ot = session.Library.one()
    for accessor in ['source']:
        code = getattr(ot, accessor)
        assert isinstance(code, Code)
        assert code.parent_id == ot.id
        assert code.name == accessor
        assert code.parent_class == "Library"


