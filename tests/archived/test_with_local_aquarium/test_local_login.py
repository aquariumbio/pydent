# import pytest
# from pydent import AqSession
# from pydent.models import *
# from marshmallow import pprint
# import uuid
# @pytest.fixture(scope='function')
# def local_session():
#     return AqSession("guest", "password", "http://0.0.0.0:3000")
#
# def test_sample(local_session):
#     sample = local_session.Sample.find(1)
#     fts = sample.sample_type.field_types
#     print(fts)
#
#     fv = sample.field_values[0]
#
#     assert fv.operation is None
#     assert isinstance(fv.parent_sample, Sample)
#     print(fv)
#     print(fv.allowable_field_type)
#
# def test_create_sample(local_session):
#
#     new_sample = Sample(name=str(uuid.uuid4()), project="MyProject", sample_type_id=1)
#     print(new_sample.dump())
#     s = local_session.utils.create_samples([new_sample])
#     print(s)
#
# def test_create_sample_type(local_session):
#
#     aqhttp = local_session._AqSession__aqhttp
#
#     st = SampleType(name='MammalianCell', description='A new mammalian cell type')
#     st.print()
#     st.field_types = []
#
#     r = aqhttp.post("sample_types.json", json_data=st.dump())
#     print(r)
#
# def test(local_session):
#
#     field_types = local_session.FieldType.all()
#     ft = field_types[1]
#     for aft in ft.allowable_field_types:
#         aft.print()
#
#     ot = OperationType(name="MyOpType", deployed=False, category="MyCategory", only_the_fly=False)
#
#     ot.field_types = [
#         local_session.FieldType(
#             name="MyPlasmid",
#             ftype="sample",
#             role="output",
#             aft_stype_and_objtype=[
#                 ("Plasmid", "Tube")
#             ]
#         )
#     ]
#
#     ot.field_types[0].allowable_field_types[0].print()
#
# def test_create_operation_type(local_session):
#
#     aqhttp = local_session._AqSession__aqhttp
#
#     ot = OperationType(name="MyOpType", deployed=False, category="MyCategory", only_the_fly=False)
#
#     ot.field_types = [
#         local_session.FieldType(
#             name="MyPlasmid",
#             ftype="sample",
#             role="output",
#             aft_stype_and_objtype=[
#                 ("Plasmid", "Tube")
#             ]
#         )
#     ]
#
#     from pydent import pprint
#     pprint(ot.dump(relations=('field_types',)))
#
#     pprint(ot.field_types[0].allowable_field_types[0].dump())
#     ot_data = ot.dump(relations={'field_types': ['allowable_field_types']})
#
#     ot_data['protocol'] = {}
#     ot_data['precondition'] = {}
#     ot_data['cost_model'] = {}
#     ot_data['documentation'] = {}
#
#     ot_data['protocol']['content'] = ''
#     ot_data['precondition']['content'] = ''
#     ot_data['cost_model']['content'] = ''
#     ot_data['documentation']['content'] = ''
#     r = aqhttp.post("operation_types.json", json_data=ot_data, allow_none=True)
#     vars(ot).update(r)
#     ot.print()
#
# # # def test_update_operation_type(local_session):
# # #
# # #     aqhttp = local_session._AqSession__aqhttp
# # #
# # #     ot = OperationType(name="MyOpType", deployed=False, category="MyCategory", only_the_fly=False)