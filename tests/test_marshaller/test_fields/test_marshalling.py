import pytest

from pydent.marshaller.base import add_schema, ModelRegistry
from pydent.marshaller.fields import Field, Nested, Relationship, Callback, Alias

from uuid import uuid4


class TestDump(object):

    def test_dump_empty_data(self, base):
        """Dump should produce an empty dictionary"""
        @add_schema
        class MyModel(base):
            pass

        model = MyModel()
        assert model.dump() == {}

    def test_dump_empty_data_with_non_tracked_attrs(self, base):
        """Expect that non-tracked attributes are excluded from the dump"""
        @add_schema
        class MyModel(base):
            pass

        model = MyModel()
        model.id = 4
        assert model.dump() == {}

    def test_dump_loaded_data(self, base):
        """Manually set data should appear in the dump"""
        @add_schema
        class MyModel(base):
            pass

        model = MyModel._set_data({"id": 5, 'name': 'MyName'})
        assert model.dump() == {"id": 5, 'name': 'MyName'}

    def test_dump_loaded_data_and_overwrite(self, base):
        """Manually set data can be overridden by setting attributes"""
        @add_schema
        class MyModel(base):
            pass

        model = MyModel._set_data({"id": 5, 'name': 'MyName'})
        model.id = 6
        assert model.dump() == {"id": 6, 'name': 'MyName'}

    def test_dump_empty_field(self, base):
        """Empty fields should return an empty dictionary"""
        @add_schema
        class MyModel(base):
            fields = dict(field=Field())

        model = MyModel()
        assert model.dump() == {}

    def test_dump_field(self, base):

        @add_schema
        class MyModel(base):
            fields = dict(field=Field())

        model = MyModel._set_data({"name": "NAME"})
        assert model.dump() == {"name": "NAME"}

    def test_dump_with_new_data_key(self, base):

        @add_schema
        class MyModel(base):
            fields = {
                "field": Field(),
                "source": Callback(lambda s: getattr(s, 'field'), callback_args=(Callback.SELF,), always_dump=True, data_key="field"),
            }

        model = MyModel({"field": 5})
        assert model.field == model.source
        print(model._get_data())
        assert model.dump() == {"field": 5}
        model.source = 6
        assert model.field == model.source
        assert model.dump() == {"field": 6}
        model.field = 7
        assert model.field == model.source
        assert model.dump() == {"field": 7}

        model = MyModel({"source": 5})
        assert model.field == model.source
        print(model._get_data())
        assert model.dump() == {"field": 5}
        model.source = 6
        assert model.field == model.source
        assert model.dump() == {"field": 6}
        model.field = 7
        assert model.field == model.source
        assert model.dump() == {"field": 7}
        print(model._get_data())

    def test_alias(self, base):
        """Expect that alias fields refer to exactly the attribute set in the alias.
        That means, the 'source' field should refer to the 'field' attribute."""
        @add_schema
        class MyModel(base):
            fields = {
                "field": Field(),
                "source": Alias("field"),
            }

        model = MyModel({"field": 5})
        assert model.field == model.source
        assert model.dump() == {"field": 5}
        model.source = 6
        assert model.field == model.source
        assert model.dump() == {"field": 6}
        model.field = 7
        assert model.field == model.source
        assert model.dump() == {"field": 7}

        model = MyModel({"source": 5})
        assert model.field == model.source
        print(model._get_data())
        assert model.dump() == {"field": 5}
        model.source = 6
        assert model.field == model.source
        assert model.dump() == {"field": 6}
        model.field = 7
        assert model.field == model.source
        assert model.dump() == {"field": 7}


    def test_dump_marshalling_field(self, base):
        """Expect the custom HTMLTag field to be properly serialized/deserialized."""
        class HTMLTag(Field):

            def serialize(self, caller, val):
                return "<{tag}>{val}</{tag}>".format(tag=self.data_key, val=val)

        @add_schema
        class MyModel(base):
            fields = dict(h1=HTMLTag())

        model = MyModel._set_data({'h1': 'raw'})
        assert model.h1 == 'raw'

        model.h1 = 'This is a Heading 1 Title'
        assert model.h1 == 'This is a Heading 1 Title'

        assert model.dump() == {'h1': '<h1>This is a Heading 1 Title</h1>'}

    def test_always_dump(self, base):
        """Expect that fields with 'always_dump' are, by default, dumped as empty
        constructors event when they are empty"""
        @add_schema
        class MyModel(base):
            fields = dict(
                field1=Callback('find'),
                field2=Callback('find', always_dump=True)
            )

            def find(self):
                return 100

        m = MyModel()

        assert m.dump() == {"field2": 100}
        assert m.dump(include='field1') == {"field1": 100, "field2": 100}
        assert m.dump(ignore='field2') == {}

    def test_empty_list_field(self, base):
        """Expect """
        @add_schema
        class ModelWithList(base):
            fields = dict(
                mylist=Field()
            )

        model = ModelWithList()
        model.mylist = []
        assert model.mylist == []
        model.mylist.append(5)
        assert model.mylist == [5]




class TestNested(object):
    """Tests for nested serialization/deserialization"""

    @pytest.fixture(scope="function")
    def Company(self, base):

        @add_schema
        class Company(base):
            pass

        return Company

    @pytest.fixture(scope="function")
    def Publisher(self, base):

        @add_schema
        class Publisher(base):

            fields = dict(author=Nested("Author"), company=Nested("Company"))

        return Publisher

    @pytest.fixture(scope="function")
    def Author(self, base):

        @add_schema
        class Author(base):

            fields = dict(publisher=Nested("Publisher"), id=Field("id", allow_none=True))

        return Author

    def test_simple_nested(self, Author, Publisher):
        author = Author._set_data({"name": "Richard Dawkings", "publisher": {"name": "Scotts Books"}})

        print(author._get_data())
        assert isinstance(author, Author)
        assert isinstance(author.publisher, Publisher)

        assert author.name == "Richard Dawkings"
        assert author.publisher.name == "Scotts Books"

    def test_double_nested(self, Author, Publisher, Company):
        author = Author._set_data({"name": "Samuel", "publisher": {"name": "Archive 81", "company": {"name": "Damage Inc."}}})

        print(author._get_data())
        assert isinstance(author, Author)
        assert isinstance(author.publisher, Publisher)
        assert isinstance(author.publisher.company, Company)

    @pytest.fixture(scope='function')
    def author_example_data(self):
        data = {"name": "Samuel", "publisher": {"name": "Archive 81", "company": {"name": "Damage Inc."}}}
        return data

    @pytest.fixture(scope='function')
    def author_example(self, author_example_data, Author, Publisher, Company):
        author = Author._set_data(author_example_data)
        return author

    def test_shared_data(self, author_example, author_example_data):

        author = author_example
        company = author.publisher.company

        print(id(author_example_data['publisher']))
        assert author_example_data['publisher'] is author._get_data()['publisher']
        print(id(author._get_data()['publisher']))
        publisher = author.publisher
        print(id(publisher._get_data()))
        assert author._get_data()['publisher'] is publisher._get_data()

    def test_double_nested_dump(self, author_example, author_example_data):
        assert author_example._get_data() == author_example_data
        assert author_example.publisher._get_data() == author_example_data['publisher']
        assert author_example.publisher.company._get_data() == author_example_data['publisher']['company']

    def test_del_nested(self, author_example, author_example_data):

        author_example.name = "TIM"
        assert author_example.name == "TIM"

        author_example.publisher.name = "Holland"
        assert author_example.publisher.name == "Holland"

        author_example.publisher.company.name = "ABC"
        assert author_example.publisher.company.name == "ABC"
        del author_example.publisher.company

        with pytest.raises(AttributeError):
            author_example.publisher.company

        assert 'company' not in author_example._get_data()['publisher']
        assert 'company' not in author_example.publisher._get_data()

    def test_set_none_on_nested(self, author_example):
        author_example.publisher = None
        assert author_example.publisher is None
        assert author_example._get_data()['publisher'] is None

    def test_set_nested_attribute(self, author_example, Publisher):
        author_example.publisher = None
        assert author_example.publisher is None
        assert author_example._get_data()['publisher'] is None
        publisher = Publisher._set_data({"name": "P"})
        author_example.publisher = publisher

        assert author_example.publisher.name == 'P'
        assert author_example._get_data()['publisher'] is publisher._get_data()

    def test_nested_dump(self, author_example, author_example_data):

        new_company_name = str(uuid4())

        expected_data = dict(author_example_data)
        expected_data['publisher']['company']['name'] = new_company_name

        author_example.publisher.company.name = new_company_name

        expected_data_copy = dict(expected_data)
        expected_data_copy.pop('publisher')
        assert expected_data_copy == author_example.dump()

        expected_data_copy = dict(expected_data['publisher'])
        expected_data_copy.pop('company')
        assert expected_data_copy == author_example.publisher.dump()

        assert expected_data['publisher']['company'] == author_example.publisher.company.dump()

    def test_load_a_model(self, base, author_example):

        @add_schema
        class AuthorList(base):
            fields = dict(author=Nested("Author"))

        author_list = AuthorList()
        author_example.publisher.company.name = "Umbrella Corp"
        author_list.author = author_example
        assert author_list.author.publisher.company.name == "Umbrella Corp"

        author_example.publisher.company.name = "LexCorp"
        assert author_list.author.publisher.company.name == "LexCorp"


class TestRelationship(object):

    @pytest.fixture(scope="function")
    def Company(self, base):

        @add_schema
        class Company(base):
            pass

        return Company

    @pytest.fixture(scope="function")
    def Publisher(self, base):

        @add_schema
        class Publisher(base):
            fields = dict(company=Relationship("Company", 'instantiate_model', 6, {"name": "MyCompany"}))

            def instantiate_model(self, model_name, model_id, name="Default"):
                return ModelRegistry.get_model(model_name)._set_data({"id": model_id, "name": name})

        return Publisher

    @pytest.fixture(scope="function")
    def Author(self, base):

        @add_schema
        class Author(base):
            fields = dict(publisher=Relationship("Publisher", 'instantiate_model', 4, {"name": "MyPublisher"}))

            def instantiate_model(self, model_name, model_id, name="Default"):
                return ModelRegistry.get_model(model_name)._set_data({"id": model_id, "name": name})

        return Author

    @pytest.mark.parametrize('model,include,expected', [
        ("Company", None, {}),
        ("Publisher", None, {}),
        ("Author", None, {}),
        pytest.param("Publisher", "company", {"company": {
            "id": 6,
            "name": "MyCompany"
        }}, id="include 1 layer nested"),
        pytest.param("Author", "publisher", {"publisher": {
            "id": 4,
            "name": "MyPublisher"
        }}, id="include 1 layer nested"),
        pytest.param(
            "Author", {"publisher": "company"}, {"publisher": {
                "id": 4,
                "name": "MyPublisher",
                "company": {
                    "id": 6,
                    "name": "MyCompany"
                }
            }},
            id="include 2 layer nested"),
    ])
    def test_nested_dump_with_include(self, base, Author, Publisher, Company, model, include, expected):
        instance = ModelRegistry.get_model(model)()
        assert instance.dump(include=include) == expected

    @pytest.mark.parametrize('model,only,expected', [
        pytest.param("Author", "publisher", {"publisher": {
            "name": "MyPublisher",
            "id": 4
        }}),
        pytest.param("Author", {"publisher": "name"}, {"publisher": {
            "name": "MyPublisher"
        }}),
        pytest.param("Author", {"publisher": "id"}, {"publisher": {
            "id": 4
        }}),
        pytest.param("Author", {"publisher": "company"}, {"publisher": {
            "company": {
                "name": "MyCompany",
                "id": 6
            }
        }}),
        pytest.param("Author", {"publisher": {
            "company": "id"
        }}, {"publisher": {
            "company": {
                "id": 6
            }
        }})
    ])
    def test_relationship_dump_with_only(self, base, Author, Publisher, Company, model, only, expected):
        instance = ModelRegistry.get_model(model)()
        assert instance.dump(only=only) == expected

    def test_relationship_dump_ignore(self, base, Author):
        instance = Author._set_data({"name": "MyName", "id": 5})
        assert instance.dump() == {"name": "MyName", "id": 5}
        assert instance.dump(ignore="name") == {"id": 5}
        assert instance.dump(ignore=["name", "id"]) == {}

    def test_basic_relationship(self, base):

        @add_schema
        class Publisher(base):
            pass

        @add_schema
        class Author(base):

            fields = dict(publisher=Relationship("Publisher", 'instantiate_model', 4, {"name": "MyPublisher"}), cache=True)

            def instantiate_model(self, model_name, model_id, name="Default"):
                return ModelRegistry.get_model(model_name)._set_data({"id": model_id, "name": name})

        author = Author()
        assert author.dump() == {}
        assert isinstance(author.publisher, Publisher), "publisher attribute should be a Publisher type"
        assert author.publisher._get_data() is author._get_data()['publisher'], "data should be shared between the Author and Publisher"

        assert author._get_data() == {"publisher": {"id": 4, "name": "MyPublisher"}}

        assert author.dump() == {}
        assert author.dump(include=["publisher"]) == author._get_data()

    def test_many_relationship(self, base):

        @add_schema
        class Publisher(base):
            pass

        @add_schema
        class Author(base):

            fields = dict(publisher=Relationship("Publisher", 'instantiate_model', 4, {"name": "MyPublisher"}, many=True))

            def instantiate_model(self, model_name, model_id, name="Default"):
                models = []
                for i in range(3):
                    models.append(ModelRegistry.get_model(model_name)._set_data({"id": model_id, "name": name}))
                return models

        author = Author()
        print(author.dump())
        print(author.dump(include="publisher"))
        assert len(author.publisher) == 3
        assert len(author.dump(include="publisher")['publisher']) == 3
        author.publisher = [Publisher._set_data({"id": 3}), Publisher._set_data({"id": 5})]

        assert len(author.publisher) == 2
        assert len(author.dump(include="publisher")['publisher']) == 2
        assert author.publisher[0].id == 3
        assert author.publisher[1].id == 5

        author.publisher.append(Publisher())
        assert len(author.publisher) == 3
        assert len(author.dump(include="publisher")['publisher']) == 3

    def test_load_relationship(self, base):
        @add_schema
        class Publisher(base):
            pass

        @add_schema
        class Author(base):

            fields = dict(publishers=Relationship("Publisher", 'instantiate_model', 4, {"name": "MyPublisher"}, many=True))

            def instantiate_model(self, model_name, model_id, name="Default"):
                models = []
                for i in range(3):
                    models.append(ModelRegistry.get_model(model_name)._set_data({"id": model_id, "name": name}))
                return models

        publisher_data = {
            "name": "Torr Books"
        }

        author = Author._set_data({
            "name": "Steven King",
            "publishers": [publisher_data]
        })

        assert len(author.publishers) == 1
        assert isinstance(author.publishers[0], Publisher)
        assert author.publishers[0]._get_data() is publisher_data
        del author.publishers

        assert len(author.publishers) == 3
        assert isinstance(author.publishers[0], Publisher)