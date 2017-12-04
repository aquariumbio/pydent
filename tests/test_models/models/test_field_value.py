import pytest

from pydent.exceptions import AquariumModelError
from pydent.models import *
from pydent.aqhttp import AqHTTP

def test_fv_simple_constructor():
    fv = FieldValue(name="something")
    print(fv)

    assert 'name' in fv.dump()
    assert fv.name is not None
    assert fv.dump()['name'] == fv.name


def test_constructor_with_sample():
    s = Sample.load({'id': 4})
    fv = FieldValue(role='input', parent_class='Operation', sample=s)
    assert fv.sample == s
    assert fv.child_sample_id == s.id


def test_constructor_with_item():
    i = Item.load({'id': 4})
    fv = FieldValue(role='input', parent_class='Operation', item=i)
    assert fv.item == i
    assert fv.child_item_id == i.id


def test_constructor_with_value():
    fv = FieldValue(role='input', parent_class='Operation', value=400)
    assert fv.value == 400


def test_constructor_with_container():
    fv = FieldValue(container=ObjectType.load({'id': 5}))
    FieldValue(container=ObjectType.load({'id': 5}), item=Item.load({'id': 4, 'object_type_id': 5}))
    with pytest.raises(AquariumModelError):
        FieldValue(container=ObjectType.load({'id': 5}), item=Item.load({'id': 4, 'object_type_id': 4}))


def test_set_item():
    """Set value should find the second AllowableFieldType"""
    fake_fv = FieldValue.load({
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
    fake_item = Item.load({
        "id": 300,
        "object_type": {"id": 3, "name": "tube"}
    })

    fake_fv.set_value(item=fake_item)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2
    assert fake_fv.child_item_id == fake_item.id
    assert fake_fv.item == fake_item
    assert fake_fv.sample is None


def test_set_sample():
    """Set value should find the second AllowableFieldType"""
    fake_fv = FieldValue.load({
        "id": 200,
        "child_item_id": None,
        "allowable_field_type_id": None,
        "allowable_field_type": None,
        'parent_class': "Operation",
        'role': 'input',
        "field_type": {
            "id": 100,
            "allowable_field_types": [
                {"id": 1, "sample_type_id": 2},
                {"id": 2, "sample_type_id": 3}  # should find this
            ]
        }
    })
    fake_sample = Sample.load({
        "id": 300,
        "sample_type_id": 3,
        "sample_type": {"id": 3}
    })

    fake_fv.set_value(sample=fake_sample)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2
    assert fake_fv.child_sample_id == fake_sample.id
    assert fake_fv.sample == fake_sample


def test_set_container():
    """Set value should find the second AllowableFieldType"""
    fake_fv = FieldValue.load({
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
                {"id": 2, "object_type_id": 300}  # should find this
            ]
        }
    })
    fake_container = ObjectType.load({
        "id": 300,
    })

    fake_fv.set_value(container=fake_container)
    assert fake_fv.allowable_field_type_id == 2
    assert fake_fv.allowable_field_type.id == 2



def test_set_sample_and_item():
    """Set value should find the second AllowableFieldType"""
    fake_fv = FieldValue.load({
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
                {"id": 2, "object_type_id": 44, "sample_type_id": 2}  # should find this
            ]
        }
    })
    fake_item = Item.load({
        "id": 55,
        "object_type_id": 44,
        "object_type": {"id": 44}
    })
    fake_sample = Sample.load({
        "id": 3,
        "sample_type_id": 2,
        'sample_type': {'id': 2}
    })

    fake_fv.set_value(item=fake_item, sample=fake_sample)


def test_set_sample_and_item_no_aft():
    """Set value should find the second AllowableFieldType"""
    fake_fv = FieldValue.load({
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
                {"id": 2, "object_type_id": 33, "sample_type_id": 2}  # should find this
            ]
        }
    })
    fake_item = Item.load({
        "id": 55,
        "object_type": {"id": 44}
    })
    fake_sample = Sample.load({
        "id": 3,
        'sample_type': {'id': 2}
    })

    with pytest.raises(AquariumModelError):
        fake_fv.set_value(item=fake_item, sample=fake_sample)


def test_compatible_items(monkeypatch, fake_session):
    """We expect compatible items to send a request to 'json/items' with data {'sid': 5, and 'oid': 33}
    after we set_value to the sample that has an id=5 and is associated with an aft with an object_type_id of 33."""
    def fake_post(self, *args, **kwargs):
        assert args[0] == 'json/items'
        assert args[1] == {'sid': 5, 'oid': 33}
        return {}

    monkeypatch.setattr(AqHTTP, "post", fake_post)

    fake_fv = FieldValue.load({
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
                {"id": 2, "object_type_id": 33, "sample_type_id": 2}  # should find this
            ]
        },
    })

    sample = Sample.load({
            "id": 5,
            'name': 'plasmid',
            'sample_type_id': 2
        })
    fake_fv.connect_to_session(fake_session)
    fake_fv.set_value(sample=sample)
    fake_fv.compatible_items()



def test_show():
    fake_fv = FieldValue.load({
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
                {"id": 2, "object_type_id": 33, "sample_type_id": 2}  # should find this
            ]
        },
    })
    sample = Sample.load({
            "id": 5,
            'name': 'plasmid',
            'sample_type_id': 2
        })
    fake_fv.set_value(sample=sample)
    fake_fv.show()


def test_wires_as_source(session):

    fv = session.FieldValue.find(520346)
    wires = fv.wires_as_source
    print(wires)

def test_wires_as_dest(session):
    fv = session.FieldValue.find(520346)
    wires = fv.wires_as_dest
    print(wires)

def test_successors(session):
    fv = session.FieldValue.find(520346)
    print(fv.successors)

def test_predecessors(session):
    fv = session.FieldValue.find(520346)
    print(fv.predecessors)