from pydent import AqSession

# login
nursery = AqSession("username", "password", "www.aquarium_nursery.url")

# find_by_name
primer = nursery.SampleType.find_by_name("Primer")

# find by id
sample = nursery.SampleType.find(1)

# find where
sample_types = nursery.SampleType.where({'name': 'Primer'})

# find all sample types
sample_types = nursery.SampleType.all()