import pytest
from pydent import AqSession
from pydent.models import (OperationType, Sample, SampleType)
import uuid

# skip tests
pytestmark = pytest.mark.skip(
    "These tests utilize a live session with alot of"
    " requests. In the future, we may want to utilize something like pyvrc"
    " to avoid sending live requests to Aquarium.")


class TestLocalLogin:
    """"""

    @pytest.fixture()
    def local_session(self):
        return AqSession("guest", "password", "http://0.0.0.0:3000")

    def test_sample(self, local_session):
        sample = local_session.Sample.find(1)
        fts = sample.sample_type.field_types
        print(fts)

        fv = sample.field_values[0]

        assert fv.operation is None
        assert isinstance(fv.parent_sample, Sample)
        print(fv)
        print(fv.allowable_field_type)

    def test_create_sample(self, local_session):

        new_sample = Sample(name=str(uuid.uuid4()), project="MyProject",
                            sample_type_id=1)
        print(new_sample.dump())
        s = local_session.utils.create_samples([new_sample])
        print(s)

    def test_create_sample_type(self, local_session):

        aqhttp = local_session._AqSession__aqhttp

        st = SampleType(name='MammalianCell',
                        description='A new mammalian cell type')
        st.print()
        st.field_types = []

        r = aqhttp.post("sample_types.json", json_data=st.dump())
        print(r)

    def test(self, local_session):

        field_types = local_session.FieldType.all()
        ft = field_types[1]
        for aft in ft.allowable_field_types:
            aft.print()

        ot = OperationType(name="MyOpType", deployed=False,
                           category="MyCategory", only_the_fly=False)

        ot.field_types = [
            local_session.FieldType(
                name="MyPlasmid",
                ftype="sample",
                role="output",
                aft_stype_and_objtype=[
                    ("Plasmid", "Tube")
                ]
            )
        ]

        ot.field_types[0].allowable_field_types[0].print()

    def test_create_operation_type(self, local_session):

        aqhttp = local_session._AqSession__aqhttp

        ot = OperationType(name="MyOpType", deployed=False,
                           category="MyCategory", only_the_fly=False)

        ot.field_types = [
            local_session.FieldType(
                name="MyPlasmid",
                ftype="sample",
                role="output",
                aft_stype_and_objtype=[
                    ("Plasmid", "Tube")
                ]
            )
        ]

        from pydent import pprint
        pprint(ot.dump(relations=('field_types',)))

        pprint(ot.field_types[0].allowable_field_types[0].dump())
        ot_data = ot.dump(relations={'field_types': ['allowable_field_types']})

        ot_data['protocol'] = {}
        ot_data['precondition'] = {}
        ot_data['cost_model'] = {}
        ot_data['documentation'] = {}

        ot_data['protocol']['content'] = ''
        ot_data['precondition']['content'] = ''
        ot_data['cost_model']['content'] = ''
        ot_data['documentation']['content'] = ''
        r = aqhttp.post("operation_types.json", json_data=ot_data,
                        allow_none=True)
        vars(ot).update(r)
        ot.print()

# # def test_update_operation_type(self, local_session):
# #
# #     aqhttp = local_session._AqSession__aqhttp
# #
# #     ot = OperationType(name="MyOpType", deployed=False,
#               category="MyCategory", only_the_fly=False)
