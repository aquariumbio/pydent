from pydent import AqSession, pprint

# login
session = AqSession.interactive()

# get the logged in user
user = session.current_user

# serialize basic attributes
pprint(user.dump())

# print user (including relationships)
user.print()

# print user (including relationships)
print(user)

# include 'groups'
user.dump(include=('groups',))

# include nested relationships


# include nested relationships with serialization options
item = session.Item.find(1000)

# serialize basic sample_type with item ids and the item id names object type names
item.dump(include={
    'sample_type': {},
    'items': {
        'object_type': {'opts': {'only': 'name'}},
        'opts': {'only': 'id'}
    }
})