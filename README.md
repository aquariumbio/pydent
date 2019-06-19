# Trident: Aquarium API Scripting

[![CircleCI](https://circleci.com/gh/klavinslab/trident/tree/master.svg?style=svg&circle-token=88677c59698d55a127a080cba9ca025cf8072f6c)](https://circleci.com/gh/klavinslab/trident/tree/master)
[![PyPI version](https://badge.fury.io/py/pydent.svg)](https://badge.fury.io/py/pydent)

Trident is the python API scripting for Aquarium.

## Documentation

[API documentation can be found here at klavinslab.org/trident](http://www.klavinslab.org/trident)

## Requirements

* Python > 3.4
* An Aquarium login

## Quick installation

Pydent can be installed using `pip3`.

```
    pip3 install pydent
```

or upgraded using

```
    pip3 install pydent --upgrade
```

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

