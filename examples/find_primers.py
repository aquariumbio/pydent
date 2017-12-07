from pydent import AqSession

# login
nursery = AqSession("username", "password", "www.aquarium_nursery.url")

# primer sample type
primer = nursery.SampleType.find_by_name("Primer")

# all primers
# nursery.set_timeout(60)  # if the request is taking a long time
primers = primer.samples
