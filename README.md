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


## Contributors:

via `git fame -wMC --excl '.(png|gif|enc)$'`

Total commits: 965
Total ctimes: 1348
Total files: 477
Total loc: 100924
| Author           |   loc |   coms |   fils |  distribution   |
|:-----------------|------:|-------:|-------:|:----------------|
| Justin Vrana     | 88573 |    295 |    275 | 87.8/30.6/57.7  |
| jvrana           | 12187 |    499 |    163 | 12.1/51.7/34.2  |
| Ben Keller       |   141 |    118 |     34 | 0.1/12.2/ 7.1   |
| Eric Klavins     |    20 |     47 |      3 | 0.0/ 4.9/ 0.6   |
| Ubuntu           |     2 |      3 |      1 | 0.0/ 0.3/ 0.2   |
| gasnew           |     1 |      1 |      1 | 0.0/ 0.1/ 0.2   |
| Devin Strickland |     0 |      2 |      0 | 0.0/ 0.2/ 0.0   |