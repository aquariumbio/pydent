[![travis build](https://img.shields.io/travis/USER/REPO.svg)](https://travis-ci.org/USER/REPO)
[![Coverage Status](https://coveralls.io/repos/github/USER/REPO/badge.svg?branch=master)](https://coveralls.io/github/USER/REPO?branch=master)
[![PyPI version](https://badge.fury.io/py/REPO.svg)](https://badge.fury.io/py/REPO)

![module_icon](images/module_icon.png?raw=true)

#### Build/Coverage Status
Branch | Build | Coverage
:---: | :---: | :---:
**master** | [![travis build](https://img.shields.io/travis/USER/REPO/master.svg)](https://travis-ci.org/USER/REPO/master) | [![Coverage Status](https://coveralls.io/repos/github/USER/REPO/badge.svg?branch=master)](https://coveralls.io/github/USER/REPO?branch=master)
**development** | [![travis build](https://img.shields.io/travis/USER/REPO/development.svg)](https://travis-ci.org/USER/REPO/development) | [![Coverage Status](https://coveralls.io/repos/github/USER/REPO/badge.svg?branch=development)](https://coveralls.io/github/USER/REPO?branch=development)



Trident
===
The API to Aquarium

Installation
---
```
cd to/trident
pip install .
```

Usage
---
```
from pydent import *

AqHTTP.create(login="username", password="password", aquarium_url="url.com")

```