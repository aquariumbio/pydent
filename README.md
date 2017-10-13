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

Node.js
---

From within the js directory, run tests as follows:

```javascript
> node test/get_sample_types.js
```
