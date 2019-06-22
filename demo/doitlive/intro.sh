# Recorded with the doitlive recorder
#doitlive shell: /bin/bash
#doitlive prompt: default
#doitlive speed: 3

```python
import pydent
session = pydent.login('neptune', 'http://0.0.0.0', 'aquarium')
session
s = session.Sample.one()
print(s)
print(s.properties)
primertype = session.SampleType.find_by_name("Primer")
newprimer = session.Sample.new(name="MyDemoPrimer", project="Demo", sample_type_id=primertype.id)
newprimer.field_values = []
newprimer.update_properties({'Anneal Sequence': 'AGGGTTCTGGGTTGTGCTGTA'})
newprimer.save()
print(newprimer.id)
exit()
```


