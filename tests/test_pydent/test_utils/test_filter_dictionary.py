# from pydent.utils import filter_dictionary
#
#
#    def test_filter_dictionary():
#        mydict = {'destination': None, 'name': 'MyPlan',
#                  'source': {"name": None, "id": 5, 'third': {}}}
#
#     h = filter_dictionary(mydict, lambda k, v: v is not None and v != [])
#     assert h == {'name': "MyPlan", 'source': {'id': 5}}
