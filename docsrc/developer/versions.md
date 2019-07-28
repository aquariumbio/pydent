# pydent change log
## 0.1.5a1
**2019-07-09T19:39:58.276296**
installation of keats

 - keats manager tool installation
 - remove warnings that occurred during plan.save() and plan.update()


## 0.1.5a
****


 - fixes a planner.open() bug


## 0.1.4a
****


 - fixes a planner.save() bug


## 0.1.3a
****


 - added pydent.login method, which returns an AqSession instance with option to input password securely. Useful for live demos.


## 0.1.2a
****


 - #### Major changes

* Planner class - a convenience class creating and editing plans in Aquarium.
* `Browser` - a convenience class for browsing Samples and other models. Includes caching and query bundling to reduce
number of queries and increase script speed.
* new queries (one, last, first)
* removed requirement of Marshmallow serialization/deserialization dependency, replaced by faster code
* Removed `marshmallow` as a serialization/deserialization library. A custom library is now used that avoids unnecessary
field validation. As a result, model `load` and `dump` is many fold faster.

#### Minor changes

* Continuous validation - Cannot set Nested/Relationship attributes to arbitrary values. E.g. `sample_type.sample = 5` will raise an Exception, but setting `sample_type.sample = mysample` will not.
  * `sample_type.sample = mysample` will also automatically set the `sample_id` attribute, since this is defined in the HasOne relationship as an attribute_key. But setting `sample_type.sample.id = 5` will not change the `sample_id` key.
* setting `None` will no longer trigger a query attempt. In previous versions, a relationship whose value was set to `None` would intialize a query attempt anytime `getattr` accessed a model attribute, using round-about exception handling to avoid errors; this made it impossible to set a relationship attribute to `None.` Now, a query will only be initiated if the key does not exist in the models underlying data. This means that data received from Aquarium will be used as expected (i.e. setting `{"sample": None}` will not try to initiate a query next time `model.sample` is called).
  * `FieldValue.set_value` now handles None values. In previous version, None values passed into set_field_value would be ignored, making it difficult to *reset* a FieldValue. For example `field_value.set_value(sample=None)` will now reset the sample value for the FieldValue instead of being ignored.
* `primary_key` will return an `id`. If `id==None`, then the `rid` is returned (e.g. `rid1023`)
* `HasOne` relationship will automatically set the corresponding model reference when setting attributes. E.g. `sample.sample_type = myst` will also automatically set `sample.sample_type_id = myst.id` since this is defined in the `HasOne` field. Similar tracking is not implemented for other relationships.

Developer changes

* `poetry` https://poetry.eustace.io/ now used as the package manager, replacing *pipenv*
* vcrpy` is used to cache and store queries for deterministic testing.
* Improved documentation.
