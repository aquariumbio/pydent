# Developer Notes

## How do requests happen?

### AqHTTP
All requests (POST, GET, PUT) happen through an pydent.aqhttp.AqHTTP
instance, which stores a login, the aquarium url, and login data. AqHTTP
makes generic requests to the Aquarium server.

### Interfaces
Rather than have direct access to AqHTTP and to avoid potentially harmful
requests to Aquarium, special request interfaces are used
to specify how these requests are made (pydent.interfaces).

There are two main interfaces:
* **ModelInterface** - used for finding models via 'find', 'find_by_name', 'all', or 'where'
* **UtilityInterface** - used for special and misc requests, such as
submitting plans, estimating plan costs, etc.

### Establishing an Interface
Interfaces are created using a pydent.aqsession.AqSession instance.
AqSession instances are created using a user's login information and stores
a particular AqHTTP instance.

For example, to establish a User Model interface and find a User with id=1:

```python
yoursession.User.find(1)
# or
yoursession.model_interface('User').find(1)
```

You can get a list of available models by `yoursession.models`

For example, to save a plan using the utility interface:

```python
yoursession.utils.save_plan(myplan)
```

Some model definitions already contain wrappers for using some interface,
for example, "Plan" contains a wrapper for saving itself.

myplan.save()
```python
myplane.save()
```

## Notes on Models

Most models can be initialized as follows:
```python
u = User()

# or
u = User(login='mylogin', name='myname')
```

Models can be pre-loaded with attributes using the `load` class method
```python
u = User.load({"name": "GI Joe", "login": 'gijoe'})

# attributes are loaded from the dictionary
assert u.name == "GI Joe"
assert u.login == "gijoe"
```

Models instantiate with the `load` method have their attribute automatically
'tracked' by the schema. For example,

```python
u = User.load({"name": "GI Joe", "login": 'gijoe'})
print(u.dump())

#>>> {"name": "GI Joe", "login": 'gijoe'}
```

To see more information about serialization/deserialization, see Serialization/Deserialization below

## Model Fields

Models inherit the 'ModelBase' baseclass and are pre-loaded with a
serialization/deserialization schema (via '@add_schema' decorator).
The attached schema controls how attributes are serialized and deserialized.

Serialization/deserialization is controlled by the models schema. A
model schema is automatically attached to models via the '@add_schema'
decorator

```python

@add_schema
class Sample(ModelBase):
    pass
```

If order for Trident to know what fields to serialize/deserialize, 'fields'
need to be defined for the model. There are a number of ways to define
fields for a model:

**Use the `load` class method**

```python
    u = User.load({'name': 'GIJoe'})
```

**Define it in the class definition using the 'fields' attribute'**
```python
@add_schema
class Sample(ModelBase):
    fields=dict(name=fields.Str())
```

**Establish in the __init__ using `super().__init__(**kwargs)` style**
```python
class Sample(ModelBase):
    def __init__(name=None):
        self.name = None
        self.id = None
        super().__init__(name=name, id=id)  # this creates a field called name
```

**Implicitly track all init attributes using `super().__init__(**vars(self))`**
```python
class Sample(ModelBase):
    def __init__(name=None):
        self.name = None
        self.id = None
        super().__init__(**vars(self))
```

### Notes on Editing or Creating Models

* models must have the `@add_schema` class decorator
* models inherit the `ModelBase` baseclass
* if defining a custom `__init__`
    * do not add positional arguments to `__init__`. The Marshaller does
    not expect any positional arguments when deserializing data. Dictionary
    arguments are ok
    * be sure to use `super().__init__`
    * if you would like to include attributes in the serialization fields
    use `super().__init__(fieldname=whatever,...)`
    * a short cut for tracking all attributes for serialization is to use
    `super().__init__(**vars(self))`
* fields (including relationships) are defined in the model's `fields` attribute,
which expects a dictionary of field_names with Field models
    * `pydent.marshaller.fields` is a module that contains a list of fields
    including Str, Int, Boolean, etc. Establishing a field this way will ensure
    that the attribute is properly validate. You'll notice that as of Dec 2017, Aquarium models
    do not use this explicitly. If the need for validation arises, we can explicitly
    define these fields

## Relationships

Relationships are special model fields that establish One-to-One, One-to-Many,
and Many-to-Many relationships between models.The relationships
use the attached model session to retrieve the models through Aquarium.
How these work isn't exactly straightforward and requires a little bit of explanation.

There are HasOne, HasMany, HasManyGeneric, and HasManyThrough relationships which
can be defined in the model definition in the 'fields' attribute. For example:

```python
@add_schema
class SamlpeType(ModelBase):
    fields=dict(samples=HasMany("Sample", ref="sample_type_id")
```

Trident will always attempt to *fullfill* relationships for attributes if possible

For example:

```python
# create empty Sample
s = Sample()

# s has no sample_type_id
assert not hasattr(s, 'sample_type_id')
assert not hasattr(s, 'sample_type')

# add sampel_type_id
s.sample_type_id = 1

# sample_type can now be found
assert isinstance(s.sample_type, SampleType)
```

If forwhatever reason the *fullfillment* fails, Trident will return None

```python
s = Sample.load({'sample_type_id': 100000000000})
assert s.sample_type is None
```

### Relationship fullfillment

The relationship fullfillment occurs through a 'callback' and 'params'
attributes defined in the relationships `__init__` definition. When
fullfilling a relationship, the model will use its 'callback' method
and pass in the 'params' value found in the relationship. The 'params' may
include callable (i.e. lambdas), in which case the model fullfilling the
relationship will pass in itself to retrieve the parameters.

As an example, the  SampleType relationship in the Sample definition:

```python
class SampleType(ModelBase):
    fields=dict(sample_type=HasMany("Sample", ref="sample_type_id")
```

The HasMany relationship defaults to the 'where_callback' method. In the
HasMany `__init__` definition, params are established such that
```python
params = lambda x: {'sample_type_id': x.id}
```

If a Sample with id=4 attempts to fullfill a sample_type relationship, it
finds the relationship params `lambda x: {'sample_type_id': x.id}`, passes
in itself such that `params={'sample_type_id': 4}`. Those params are passed
to the callback along with the model name

 `SampleType.where_callback('Sample', {'sample_type_id': 4})`.

'where_callback' then
uses a session instance to find Samples where {'sample_type_id': 4}.

You can also define custom callbacks for any relations. An example of this
is the FieldType model with the operation_type and sample_type fields.

## Serialization/Deserialization

### Serialization

load
load only

### Deserialization

dump only
dump relations
dump all_relations
dump only dictionary

### Request History

In an attempt to minimize unnecessary requests to Aquarium, Trident
stores a 'request_history' in pydent.aqhttp.request_history. This means,
for 'find', 'find_by_name', and 'where' will not make a new request if
an equivalent request has been previously made. Request history can
be cleared using `session.clear_history()`

I'm currently iffy on whether we should keep this behavior or not.
