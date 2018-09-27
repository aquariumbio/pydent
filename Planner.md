Planner Setter Rules:

`set_field_value` - if setting a sample, the sample will be routed via the routes indicated in the 
OperationType's FieldTypes

`set_field_value_and_propogate` - if setting a sample, the sample will be routed along *sample* routes, 
which are a combination of the OperationType's internal sample routing and external Operation to Operation wires.

`set_output` - will map sample field values to inputs if possible

`set_output(fv, sample, setter=plan.set_field_value_and_propogate)` - same as set_output, but will also
propogate each input and output it sets.

`add_wire` - Used in quick_wire, quick_create_chain, etc. The method will inherit sample from source to destination. If source field_value already has a allowable_field_type
defined and it is possible to wire with that allowable_field_type (meaning the destination field_value has a matching
allowable_field_type), the planner will prefer to choose that allowable_field_type that was set in the source field_value.
Else it will choose the first matching allowable_field_type

`quick_wire` - Will try to wire the source to the destination. The source/destination can either
be FieldValue or Operation. In the case that they are operations, the planner will look for the 
next empty field value that can be wired and wire it. If there are no more empty field values, an 
error will be raised. If the input is an array, a new field value will be created and this new field
value will be wired. The allowable_field_type and sample will be inherited according to the `add_wire`
rules.

`quick_create_chain` - Will wire existing operations, existing field values, or create new operations
 (if strings) and wire those together according to the `quick_wire` rules.