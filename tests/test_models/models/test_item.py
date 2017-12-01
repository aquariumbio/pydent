

def test_item_data(session):
    item = session.Item.find(114553)
    data = item.data
    print(type(data))
