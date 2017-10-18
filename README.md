Trident
===
The API to Aquarium

Python
---

To get started, first change to the py directory. Next copy config_template.py to config.py and edit the contents of the new file to suit your situation. Finally, make sure that Python can find the directory by doing

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/trident/py
```

Next, run the tests in the test directory as follows:

```python
> python test/basics.py
```

#### Importing
```python
from pydent import *
```

#### Starting pydent sessions and logging in
```python
Session.create(login="JMellencamp",
                   password="Hurt5S0G0OD",
                   aquarium_url="http://521.124.511")
```

You can name you sessions
```python
Session.create(login="JMellencamp",
                   password="Hurt5S0G0OD",
                   aquarium_url="http://521.124.511",
                   name="Nursery")

Session.create(login="JMellencamp",
                   password="Hurt5S0G0OD",
                   aquarium_url="http://521.124.52464",
                   name="Production")
```

Switching sessions
```python
# Set sessions by name
Session.set("Production")
# do production stuff here
Session.set("Nursery")
# do nursery stuff here

# hook for setting sessions
Session.Nursery
# do production stuff here
Session.Production
# do nursery stuff here
```

You can create sessions from a json file. Say you have a json file name "config.json"
```json
{
  "Nursery": {
    "aquarium_url": "http://23.274.443.2442:85",
    "login": "Joe",
    "password": "secret_password"
  },
  "Production": {
    "aquarium_url": "http://23.274.443.2442",
    "login": "Joe2",
    "password": "password2"
  }
}
```
You can import sessions using:
```python
Session.create_from_config_file("config.json")
# automatically sets to last session in the file
# but you can switch using
Session.set("Nursery")
```

Node.js
---

From within the js directory, run tests as follows:

```javascript
> node test/get_sample_types.js
```
