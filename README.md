# Trident: Aquarium API Scripting

Trident is the python API scripting for Aquarium.
More extensive documentation can be found here: [Documentation](docs/index.html)
Other documents can be found in the links below.

1. [Documentation](docs/index.html)
2. [Examples](Examples.md)
3. [Developer Notes](DeveloperNotes.md)
3. [Tests](Tests.md)

## Installation

1. Clone or download this repo from https://github.com/klavinslab/trident
2. cd to directory containing trident
3. run `pip install .` or `pip install . --upgrade`

## Basic Usage

### Logging in
```python
from pydent import AqSession

# open a session
mysession = AqSession("username", "password", "www.aquarium_nursery.url")

# find a user
u = mysession.User.find(1)

# print the user data
print(u)
```

### Models
```python
print(mysession.models)
```

#### Finding models

**find_by_name** - `nursery.SampleType.find_by_name("Primer")`

**find by id** - `nursery.SampleType.find(1)`

**where** - `nursery.SampleType.where({'name': 'Primer'})`

**all** - `nursery.SampleType.all()`


**Getting nested data**
```python
# samples are linked to sample_type
primer_type = mysession.SampleType.find_by_name("Primer")
primers = primer_type.samples

# and sample type is linked to sample
p = primers[0]
print(p.sample_type)
```

**Available nested relationships**
```python
primer_type = mysession.SampleType.find(1)
print(primer_type.relationships)
```
