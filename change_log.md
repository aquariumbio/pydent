# Change Log

### 0.1.0

#### Features 

* Removed `marshmallow` as a serialization/deserialization library. A custom library is now used that avoids unnecessary field validation. As a result, model `load` and `dump` is faster.

* `Browser` - a convinience method for browsing Samples and other models. Includes cacheing and query bundling to reduce number of queries and increase script speed.

  ##### Testing/Docs

  * vcrpy` is used to cache and store queries for deterministic testing.
  * Improved documentation.
  * Testing pytest-benchmarks (TODO: store previous versions)

#### API Changes

* Continuous validation - Cannot set Nested/Relationship attributes to arbitrary values. E.g. `sample_type.sample = 5` will raise an Exception, but setting `sample_type.sample = mysample` will not. 
* Automatic setting of primary_keys (TODO):

  * `sample_type.sample = mysample` will also automatically set the `sample_id` attribute, since this is defined in the HasOne relationship as an attribute_key. But setting `sample_type.sample.id = 5` will not change the `sample_id` key.
* setting `None` will no longer trigger a query attempt. In previous versions, a relationship whose value was set to `None` would intialize a query attempt anytime `getattr` accessed a model attribute, using round-about exception handling to avoid errors; this made it impossible to set a relationship attribute to `None.` Now, a query will only be initiated if the key does not exist in the models underlying data. This means that data received from Aquarium will be used as expected (i.e. setting `{"sample": None}` will not try to initiate a query next time `model.sample` is called).

  * tldr;
    * Use: `del model.attr` will reset model to trigger a query
    * Settings `model.attr = None` will not trigger a query next time `model.attr` is called.
    * Data used to load models will be used as is (e.g. `{'sample': None}` will not initiate a query if `model.sample` is called)
* Setting FieldValue (TODO)

  * `FieldValue.set_value` now handles None values. In previous version, None values passed into set_field_value would be ignored, making it difficult to *reset* a FieldValue. For example `field_value.set_value(sample=None)` will now reset the sample value for the FieldValue instead of being ignored.
* `primary_key` will return an `id`. If `id==None`, then the `rid` is returned (e.g. `rid1023`)
* `HasOne` relationship will automatically set the corresponding model reference when setting attributes. E.g. `sample.sample_type = myst` will also automatically set `sample.sample_type_id = myst.id` since this is defined in the `HasOne` field. Similar tracking is not implemented for other relationships.
* Setting arrays has changed. Due to the way deserialization takes place, setting a 

### Code Changes

* Model constructors `__init__` are much cleaner. Simply pass kwargs to `super().__init__` to initialize serialization/deserialization data. Kwargs passed to `super().__init__` will automatically be expected to be dumped. Due to the deserialization/serialization process, the **order** of the kwargs in `super().__init__` does matter.
* `id` and `rid` (model instance counter) is automatically tracked by default. All models that are subclassed from `ModelBase` will have an `id` and `rid` 
* There is no longer any real field validation. Marshamallow has been removed as a dependency. This is because, in Trident's case, data received from Aquarium is assumed to always be pre-validated. For the most part, data sent to Aquarium should be validated on server side. Validation steps marshmallow was performing was unnecessary and slowing loading and dumping of models. Serialization/deserialization has been entirely re-written to be cleaner and more predictable.


#### TODO

* on version change, run benchmark, store latest run and save
* move benchmark images to documentation
* `AutoPlanner`



      ```
(?<!fake_session)(\w+).load\(       fake_session.$1.load(
      ```

```
(?<!fake_session)(\.\w+).load\(       fake_session$1.load(
```

