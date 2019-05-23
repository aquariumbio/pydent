class TestItem(object):

    def test_field_values_as_output(self, session):
        fv = None
        for fv in session.FieldValue.last(100, query=dict(role="output")):
            if fv.child_item_id:
                break
        assert fv, "There should be a FieldValue with an item for this test"

        item = fv.item
        assert len(item.field_values_as_outputs) > 0

    def test_field_values_as_input(self, session):
        fv = None
        for fv in session.FieldValue.last(100, query=dict(role="input")):
            if fv.child_item_id:
                break
        assert fv, "There should be a FieldValue with an item for this test"

        item = fv.item
        assert len(item.field_values_as_inputs) > 0

    def test_operations_as_output(self, session):
        fv = None
        for fv in session.FieldValue.last(100, query=dict(role="output")):
            if fv.child_item_id:
                break
        assert fv, "There should be a FieldValue with an item for this test"

        item = fv.item
        assert len(item.operations_as_outputs) > 0

    def test_operations_as_input(self, session):
        fv = None
        for fv in session.FieldValue.last(100, query=dict(role="input")):
            if fv.child_item_id:
                break
        assert fv, "There should be a FieldValue with an item for this test"

        item = fv.item
        assert len(item.operations_as_inputs) > 0
