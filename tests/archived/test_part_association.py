from pydent import models

def test_part_association_exists(session):
    pas = session.PartAssociation.where({}, opts={"limit": 50})
    part_association = pas[-1]

    assert isinstance(part_association.collection, models.Collection)
    assert isinstance(part_association.part, models.Item)
    assert len(part_association.collection.parts) > 0
    assert isinstance(part_association.collection.parts[0], models.Item)