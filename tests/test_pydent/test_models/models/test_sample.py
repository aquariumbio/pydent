import pytest


# def test_update_properties_to_none(example_sample):
#
#     assert example_sample.properties['Length']
#
#     example_sample.update_properties({"Length": None})
#
#     assert not example_sample.properties['Length']


@pytest.mark.parametrize(
    "num_field_values",
    list(range(10)),
    ids=["{} field values".format(x) for x in range(10)],
)
def test_update_properties_of_field_value_array(example_sample, num_field_values):
    # fake_sample.field_value_array
    example_sample.set_field_value_array(
        "Fragment Mix Array", None, [{"sample": example_sample}] * num_field_values
    )
    assert (
        len(example_sample.field_value_array("Fragment Mix Array")) == num_field_values
    )

    # reset field values
    example_sample.set_field_value_array(
        "Fragment Mix Array",
        None,
        [{"sample": example_sample}] * (10 - num_field_values),
    )
    assert (
        len(example_sample.field_value_array("Fragment Mix Array"))
        == 10 - num_field_values
    )


@pytest.mark.parametrize(
    "num_field_values",
    list(range(1)),
    ids=["{} field values".format(x) for x in range(1)],
)
def test_update_properties_using_array(example_sample, num_field_values):
    # fake_sample.field_value_array
    example_sample.update_properties(
        {"Fragment Mix Array": [example_sample] * num_field_values}
    )
    assert (
        len(example_sample.field_value_array("Fragment Mix Array")) == num_field_values
    )

    # reset field values
    example_sample.update_properties(
        {"Fragment Mix Array": [example_sample] * (10 - num_field_values)}
    )
    assert (
        len(example_sample.field_value_array("Fragment Mix Array"))
        == 10 - num_field_values
    )


def test_copy_sample(example_sample):

    props = example_sample.properties

    copied = example_sample.copy()
    props2 = copied.properties
    assert copied.id is None
    assert (
        copied.properties["Reverse Primer"].id
        == example_sample.properties["Reverse Primer"].id
    )
    assert not id(copied.properties["Reverse Primer"]) == id(
        example_sample.properties["Reverse Primer"]
    )
