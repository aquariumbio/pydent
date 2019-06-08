import pytest

from pydent.aqhttp import AqHTTP
from pydent.exceptions import AquariumModelError
from pydent.models import (FieldValue, FieldType)


def test_fv_simple_constructor(fake_session):
    fv = fake_session.FieldValue.new(name="something")
    print(fv)

    assert fv, "Field value should be non-null"
    assert 'name' in fv.dump()
    assert fv.name is not None
    assert fv.dump()['name'] == fv.name


def test_constructor_with_sample(fake_session):
    s = fake_session.Sample.load({'id': 4})
    fv = FieldValue(role='input', parent_class='Operation', sample=s)
    assert fv.sample == s
    assert fv.child_sample_id == s.id


def test_constructor_with_item(fake_session):
    i = fake_session.Item.new()
    fv = fake_session.FieldValue.new(role='input', parent_class='Operation', item=i)
    assert fv.item == i
    assert fv.child_item_id == i.id


def test_constructor_with_value(fake_session):
    fv = fake_session.FieldValue(
        role="input",
        parent_class="Operation",
        value=400,
        field_type=fake_session.FieldType(
            choices='400',
            parent_class='OperationType'
        )
    )
    assert fv.value == 400


def test_raises_exception_with_wrong_choice(fake_session):
    fv = fake_session.FieldValue.load(dict(
        role='input', parent_class='Operation', value=400, field_type=dict(choices='400,301', id=5)
    ))
    fv.set_value(value=301)
    assert fv.value == 301
    with pytest.raises(AquariumModelError):
        fv.set_value(value=300)


def test_constructor_with_container(fake_session):
    # TODO what's the test here? there are no assertions
    fv = fake_session.FieldValue.new(container=fake_session.ObjectType.load({'id': 5}))
    fv_with_container = fake_session.FieldValue.new(container=fake_session.ObjectType.load({'id': 5}),
               item=fake_session.Item.load({'id': 4, 'object_type_id': 5}))
    assert fv_with_container.object_type.id == 5
    with pytest.raises(AquariumModelError):
        fake_session.FieldValue.new(container=fake_session.ObjectType.load(
            {'id': 5}), item=fake_session.Item.load({'id': 4, 'object_type_id': 4}))


def test_set_item(fake_session):
    """Set value should find the second AllowableFieldType"""
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 2},
                {"id": 2, "object_type_id": 3}  # should find this
            ]
        }
    })
    fake_item = fake_session.Item.load({
        "id": 300,
        "object_type": {"id": 3, "name": "tube"}
    })

    fake_fv.set_value(item=fake_item)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2
    assert fake_fv.child_item_id == fake_item.id
    assert fake_fv.item == fake_item
    assert fake_fv.sample is None


def test_set_sample(fake_session):
    """Set value should find the second AllowableFieldType"""
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        'object_type': None,
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "sample_type_id": 2},
                {"id": 2, "sample_type_id": 3}  # should find this
            ]
        }
    })
    fake_sample = fake_session.Sample.load({
        "id": 300,
        "sample_type_id": 3,
        "sample_type": {"id": 3}
    })

    fake_fv.set_value(sample=fake_sample)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2
    assert fake_fv.child_sample_id == fake_sample.id
    assert fake_fv.sample == fake_sample


def test_set_container(fake_session):
    """Set value should find the second AllowableFieldType"""
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'child_sample_id': None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 2},
                {"id": 2, "object_type_id": 300}  # should find this
            ]
        }
    })
    fake_container = fake_session.ObjectType.load({
        "id": 300,
    })

    fake_fv.set_value(container=fake_container)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2


def test_set_sample_and_item(fake_session):
    """Set value should find the second AllowableFieldType"""
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 2, "sample_type_id": 3},
                {"id": 2, "object_type_id": 44,
                    "sample_type_id": 2}  # should find this
            ]
        }
    })
    fake_item = fake_session.Item.load({
        "id": 55,
        "object_type_id": 44,
        "object_type": {"id": 44}
    })
    fake_sample = fake_session.Sample.load({
        "id": 3,
        "sample_type_id": 2,
        'sample_type': {'id': 2}
    })

    fake_fv.set_value(item=fake_item, sample=fake_sample)


def test_set_sample_and_item_no_aft(fake_session):
    """Set value should find the second AllowableFieldType"""
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "name": "My input",
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 44, "sample_type_id": 3},
                {"id": 2, "object_type_id": 33,
                    "sample_type_id": 2}  # should find this
            ]
        }
    })
    fake_item = fake_session.Item.load({
        "id": 55,
        "object_type": {"id": 44, "name": "MySampleType"}
    })
    fake_sample = fake_session.Sample.load({
        "id": 3,
        'sample_type': {'id': 2, "name": "MySampleType2"}
    })

    with pytest.raises(AquariumModelError):
        fake_fv.set_value(item=fake_item, sample=fake_sample)


def test_compatible_items(monkeypatch, fake_session):
    """
    We expect compatible items to send a request to 'json/items' with data
    {'sid': 5, and 'oid': 33}
    after we set_value to the sample that has an id=5 and is associated with
    an aft with an object_type_id of 33.
    """

    def fake_post(self, *args, **kwargs):
        assert args[0] == 'json/items'
        assert args[1] == {'sid': 5, 'oid': 33}
        return {}

    monkeypatch.setattr(AqHTTP, "post", fake_post)

    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 44, "sample_type_id": 3},
                {"id": 2, "object_type_id": 33,
                    "sample_type_id": 2}  # should find this
            ]
        },
    })

    sample = fake_session.Sample.load({
        "id": 5,
        'name': 'plasmid',
        'sample_type_id': 2
    })
    fake_fv.set_value(sample=sample)
    fake_fv.compatible_items()


def test_show(fake_session):
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        'name': 'my_fake_fv',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 44, "sample_type_id": 3},
                {"id": 2, "object_type_id": 33,
                    "sample_type_id": 2}  # should find this
            ]
        },
    })
    sample = fake_session.Sample.load({
        "id": 5,
        'name': 'plasmid',
        'sample_type_id': 2
    })
    fake_fv.set_value(sample=sample)
    fake_fv.show()


def test_dump(fake_session):
    fake_fv = fake_session.FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        'name': 'my_fake_fv',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "object_type_id": 44, "sample_type_id": 3},
                {"id": 2, "object_type_id": 33,
                    "sample_type_id": 2}  # should find this
            ]
        },
    })
    sample = fake_session.Sample.load({
        "id": 5,
        'name': 'plasmid',
        'sample_type_id': 2
    })
    fake_fv.set_value(sample=sample)
    fake_dump = fake_fv.dump()
    assert fake_dump['sid'] == fake_fv.sid


# def test_wires_as_source(session):
#    fv = session.FieldValue.find(520346)
#    assert fv, "FieldValue 520346 not found"
#    wires = fv.wires_as_source
#    print(wires)


# def test_wires_as_dest(session):
#    fv = session.FieldValue.find(520346)
#    assert fv, "FieldValue 520346 not found"
#    wires = fv.wires_as_dest
#    print(wires)


# def test_successors(session):
#    fv = session.FieldValue.find(520346)
#    assert fv, "FieldValue 520346 not found"
#    print(fv.successors)


# def test_predecessors(session):
#    fv = session.FieldValue.find(520346)
#    assert fv, "FieldValue 520346 not found"
#    print(fv.predecessors)
