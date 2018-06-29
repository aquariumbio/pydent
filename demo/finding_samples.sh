```python
from pydent import AqSession

session = AqSession.interactive()

sample = session.Sample.find(1)

sample.print()

sample.field_values

sample.field_values.name

sample.field_values.print()

sample.dump()

sample.print(all_relations=True)

sample.print(include=['field_values', 'sample_type'])

```