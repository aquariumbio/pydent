from uuid import uuid4


def test_weird_data_association_retrieval_bug(session):

    item = session.Item.one()

    das1 = item.data_associations
    d1 = id(das1)
    das2 = item.data_associations
    das3 = item.data_associations
    for _ in [das1, das2, das3]:
        print(id(_))
    assert id(das1) == id(das2)


def test_create_data_association(session):

    item = session.Item.one()

    # create random uuid value
    val = str(uuid4())
    _da = item.associate('test_association', val)

    da = item.data_associations[-1]

    assert da.value == val

    reloaded = session.Item.find(item.id)

    for da in reloaded.data_associations:
        print(da.value)

    assert reloaded.data_associations[-1].value == val