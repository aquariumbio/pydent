from pydent.marshaller import add_schema
from pydent.relationships import HasMany
from pydent import ModelBase, pprint
from pydent.models import *


def test_attribute_missing():
    @add_schema
    class Author(ModelBase):
        fields = dict(books=HasMany("Book", ref="book_id", callback="foo"))

        def __init__(self):
            self.books = None

        def foo(self, *args):
            print(args)

    class Book(ModelBase):
        pass

    a = Author.load({})
    print(a.books)
    print(a.dump())


def test_nested_dump_relations():

    ot = OperationType(name="MyOT")
    aft = AllowableFieldType(object_type=ObjectType(id=1, name="MyOBJ"), sample_type=SampleType(id=2, name="MYSAMPLETYPE"))
    ot.field_types = [FieldType(name="MyFV", allowable_field_types=[aft])]
    ot.operations = []
    #
    # # dump with 'field_types' and 'allowable_field_types'
    # expected = ot.dump()
    # ft = ot.field_types[0]
    # ft_data = ft.dump()
    # aft = ft.allowable_field_types[0]
    # ft_data['allowable_field_types'] = [aft.dump()]
    # expected['field_types'] = [ft_data]
    # #
    # assert expected == ot.dump(relations={'field_types': ['allowable_field_types']})
    #
    # # also dump with object_type
    # expected['field_types'][0]['allowable_field_types'][0]['object_type'] = aft.object_type.dump()
    print()
    # pprint(ot.dump(relations={'field_types': {'allowable_field_types': 'object_type'}}))
    ot.dump(relations={'field_types': ['allowable_field_types']})
    # schema = ot.create_schema_instance(dump_relations={'field_types': {'allowable_field_types': 'object_type'}})
    print()
    print()
    pprint(ot.dump(relations={'field_types': {'allowable_field_types': 'object_type'}}))
    # pprint(expected)
    # assert expected == ot.dump(relations={'field_types': {'allowable_field_types': 'object_type'}})