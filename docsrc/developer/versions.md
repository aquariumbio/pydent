# pydent change log
## 0.1.5a8
**2019-11-19T18:33:38.350971**
bug fixes

 - fixes loggable class and adds tests
 - fixes issue with attribute access in session
 - fixes issue whe3re Plan.one() return None for Aquarium 2.7
 - Plan no longer includes wires on query


## 0.1.5a6
**2019-08-08T14:52:14.631040**





## 0.1.5a5
**2019-08-08T14:43:40.229011**
bug fix

 - fixes bug with field values that have no operations when using planner.set_to_available_item


## 0.1.5a4
**2019-08-08T14:37:26.698386**
bug fix with setting available items

 - fixed RESTRICT_TO_ONE for item_preference in planner
 - added RESTRICT_TO_ONE_ON_SERVER that looks at all reserved items on the server


## 0.1.5a3
**2019-08-06T14:42:09.748998**
bug fixes

 - fixes find(id=0) bug that raised a mysterious error
 - session.<Model>.all() no longer raises error when cache is being used


## 0.1.5a2
**2019-07-28T13:08:07.331007**
minor bug fixes

 - Fixed error that occurred when Planner and PlannerLayout had no operations
 - Added 'using_verbose' to session factory. Create a verbose session using `session(using_verbose=True)`
 - Improved logging library. Logging library accessible via '<model>.log' as in `session.log.info(<msg>)`
 - Traceback limit for logging can be set using `session.log.set_tb_limit(<limit>)`


## 0.1.5a1
**2019-07-26T08:46:10.461557**
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
