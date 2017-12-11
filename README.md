# Trident: Aquarium API Scripting

Trident is the python API scripting for Aquarium.

1. [Examples](Examples.md)
1. [Developer Notes](DeveloperNotes.md)
1. [Tests](Tests.md)
1. [Updating Documentation](CreatingDocs.md)

API documentation is located in `docs/index.html`.

## Requirements

* Python > 3.4
* an Aquarium login

## Installation

1. Clone or download [this repo](https://github.com/klavinslab/trident)
1. cd to directory containing trident
1. run `pip install .` or `pip install . --upgrade`

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

* By name: `nursery.SampleType.find_by_name("Primer")`

* By ID: `nursery.SampleType.find(1)`

* By property: `nursery.SampleType.where({'name': 'Primer'})`

* All models: `nursery.SampleType.all()`

#### Getting nested data

```python
# samples are linked to sample_type
primer_type = mysession.SampleType.find_by_name("Primer")
primers = primer_type.samples

# and sample type is linked to sample
p = primers[0]
print(p.sample_type)
```

#### Available nested relationships

```python
primer_type = mysession.SampleType.find(1)
print(primer_type.relationships)
```
