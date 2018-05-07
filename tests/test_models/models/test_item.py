

def test_item_data(session):
    item = session.Item.find(114553)
    assert item, "Item 114553 not found"
    data = item.data
    print(type(data))
